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
import ipaddress
import json
import math
import os
import re
import sys
import unicodedata
import urllib.parse

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "templates", "taxonomy.json")
PROJECT_TAXONOMY_REL = os.path.join(".claude", "knowledge-services", "taxonomy.json")

VERSIONES_SOPORTADAS = (1,)
ROUTING_VALORES = (True, False, "summary")

# `backends.<id>.config` de `type: "graphiti"` (graphiti-memory T-01, ADR-018 enmienda 2026-09-17,
# CA-09/CA-10/CA-12/CA-13). Validación ESTÁTICA de configuración (no hace red ni DNS): distinta
# del check runtime con resolución DNS de `backends/markdown_export.py::_host_permitido`, que
# vive en el adaptador porque necesita seguir redirecciones reales.
GRAPHITI_MODE_VALORES = ("off", "shadow", "read")
GRAPHITI_PROVIDER_LLM_VALORES = ("ollama", "openai", "anthropic", "none")
# Claves reconocidas de `backends.<id>` (todos los tipos) y de `backends.<id>.config` para
# `type: "graphiti"` — enmienda 2026-09-19 de design.md (gap #1/#14 de la revisión de la Fase 1):
# cualquier clave fuera de estos conjuntos es ERROR, no se ignora en silencio.
_BACKEND_CLAVES = ("type", "enabled", "config")
_GRAPHITI_CONFIG_CLAVES = (
    "mode", "endpoint", "group_id", "allow_remote", "provider", "entity_map",
    "relations", "router", "telemetria", "health", "timeout_ms", "concurrency",
    "episode_body_max_kb", "max_respuesta_kb", "max_episodes",
)
_GRAPHITI_PROVIDER_CLAVES = ("llm", "model", "embedder", "embedder_model", "base_url", "api_key_env")
_GRAPHITI_ROUTER_CLAVES = ("intents", "default")
_GRAPHITI_HEALTH_CLAVES = ("url", "timeout_ms")
# Nombre de variable de entorno: mismo alfabeto que un identificador de shell POSIX habitual.
# Un valor con espacios o que empiece por dígito no es un nombre de variable — es, casi siempre,
# un secreto pegado por error donde solo debía ir el NOMBRE de la variable que lo contiene (CA-09).
_ENV_VAR_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


# --8<-- hosts locales COMPARTIDO (graphiti-memory T-01-fix1) — REPLICADO LITERAL en skills/knowledge-services/backends/markdown_export.py, agent-kits/shared/knowledge-schema.py y skills/knowledge-services/backends/graphiti.py
_SUFIJOS_LOCALES = (".test", ".local", ".internal")
_HOSTS_LOCALES_LITERALES = {"localhost", "host.docker.internal"}
# --8<-- fin hosts locales COMPARTIDO


# --8<-- direccion prohibida siempre COMPARTIDO (graphiti-memory T-04-fix4, gaps #71/#75) - REPLICADO LITERAL en skills/knowledge-services/backends/graphiti.py y agent-kits/shared/knowledge-schema.py
def _normalizar_ip(ip):
    """Desenvuelve las formas de TRANSICION IPv6 -> IPv4 antes de clasificar una direccion:
    IPv4-mapeada (`::ffff:169.254.169.254`, gap #53), 6to4 (`2002::/16`, gap #71) y Teredo
    (`2001:0::/32`, gap #71; se toma la direccion del CLIENTE, que es la que de verdad se
    contacta). CPython clasifica esas tres formas mirando SOLO el prefijo IPv6 nativo, asi que
    sin desenvolverlas un `2002:a9fe:a9fe::1` (= el endpoint de metadatos `169.254.169.254`) es
    `is_private=True` y se cuela por el guardarrail de red (CWE-918)."""
    mapeada = getattr(ip, "ipv4_mapped", None)
    if mapeada is not None:
        return mapeada
    seis_a_cuatro = getattr(ip, "sixtofour", None)
    if seis_a_cuatro is not None:
        return seis_a_cuatro
    teredo = getattr(ip, "teredo", None)
    if teredo is not None:
        return teredo[1]
    return ip


def _es_transicion_ipv6(ip):
    """True si `ip` es 6to4 o Teredo. Ninguna de las dos es nunca un endpoint local legitimo de
    este proyecto (el invariante es `localhost`/red privada), y las dos las clasifica CPython
    como privadas por su prefijo: se rechazan como clase, no solo cuando lo que envuelven es una
    direccion prohibida."""
    return getattr(ip, "sixtofour", None) is not None or getattr(ip, "teredo", None) is not None


def _direccion_prohibida_siempre(ip):
    """Link-local (`169.254.0.0/16`, `fe80::/10`, tipico endpoint de metadatos de nube), no
    especificada (`0.0.0.0`, `::`) y prefijos de transicion IPv6 (6to4/Teredo) se rechazan
    SIEMPRE, incluso con `allow_remote: true` (gaps #34c y #71): `allow_remote` autoriza salir a
    redes remotas, no a la red de metadatos del propio host ni a direcciones sin sentido como
    destino de conexion."""
    if _es_transicion_ipv6(ip):
        return True
    ip = _normalizar_ip(ip)
    return bool(ip.is_link_local or ip.is_unspecified)
# --8<-- fin direccion prohibida siempre COMPARTIDO


def _endpoint_es_local(endpoint):
    """True si el host de `endpoint` es literalmente loopback/privado, o uno de los hosts/sufijos
    locales reconocidos sin resolución DNS (`_HOSTS_LOCALES_LITERALES`/`_SUFIJOS_LOCALES`, mismo
    criterio que el adaptador Kwipu — gap 15 de la revisión de la Fase 1) — validación de config
    en frío, no en tiempo de conexión. Un hostname no-IP fuera de esas listas (p. ej.
    `mi-graphiti.local` sin el sufijo `.local`... en realidad SÍ lo cubre; algo como
    `mi-graphiti.example.com`) no puede afirmarse local sin resolver, así que NO cuenta como local
    aquí (fail-closed: exige `allow_remote: true` para ese caso)."""
    try:
        parsed = urllib.parse.urlparse(endpoint)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    if host in _HOSTS_LOCALES_LITERALES or host.endswith(_SUFIJOS_LOCALES):
        return True
    try:
        ip = _normalizar_ip(ipaddress.ip_address(host))
    except ValueError:
        return False
    return bool(ip.is_loopback or ip.is_private)


def _url_con_direccion_prohibida(url):
    """Gap #75 (Important, CWE-1287): defensa en profundidad — la MISMA regla que el adaptador
    aplica en tiempo de conexion (`_direccion_prohibida_siempre`: link-local/metadatos de nube,
    direccion no especificada y prefijos de transicion IPv6) tiene que rechazar la config en
    FRIO. Antes, `endpoint: http://169.254.169.254/mcp` validaba sin error (el link-local IPv4 es
    `is_private` para CPython) mientras el adaptador lo rechazaba SIEMPRE: el usuario se llevaba
    el "no" en ejecucion, no al validar."""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False  # un nombre no se resuelve aqui (validacion en frio): lo hace el adaptador
    return _direccion_prohibida_siempre(ip)


def _url_parseable(url):
    """Gap #63 (Minor, doble fail-open): `_url_con_userinfo` fail-abre a `False` (no hay
    userinfo) ante una URL que `urlsplit` no puede interpretar (p. ej. un `[` suelto en el
    userinfo), así que una URL de ese tipo saltaba el chequeo de credenciales embebidas y caía
    directa al chequeo de host local, que SÍ interpolaba la URL cruda (con las credenciales) en
    el mensaje de error. Se rechaza explícitamente cualquier URL no parseable ANTES de esos dos
    chequeos, sin repetir la URL en el mensaje."""
    try:
        urllib.parse.urlparse(url)
        return True
    except ValueError:
        return False

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


def _url_con_userinfo(url):
    """True si `url` lleva credenciales embebidas (`http://svc:TOKEN@host/…`, gap #43 de la
    revisión Fase 2 intento 1): nunca debe aceptarse en `endpoint`/`health.url` — viajarían
    verbatim en mensajes de error/`detalle` de `graphiti.py`. Fail-open a False ante URL
    ilegible: el resto de comprobaciones (forma http(s), host local) ya la rechazan."""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False
    return bool(parsed.username or parsed.password)


def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}


def _numero_finito_mayor_que(valor, minimo):
    """True si `valor` es un `int` FINITO (nunca `bool`, que es subclase de `int`) y
    estrictamente mayor que `minimo` (T-01-fix2 gap #19/#21: los `timeout_ms` del contrato son
    milisegundos ENTEROS — `int > 0`, nunca un `float`). Antes, `health.timeout_ms` aceptaba
    cualquier `int`/`float` y solo comprobaba `timeout_ms <= 0`, y toda comparación con `NaN` es
    `False` en Python: `float('nan')` y `float('inf')` pasaban el chequeo sin que
    `socket.settimeout` pudiera aceptarlos en runtime; un `float` subnormal como `1e-09` también
    colaba como "> 0" aunque no representa milisegundos enteros con sentido."""
    if isinstance(valor, bool) or not isinstance(valor, int):
        return False
    return math.isfinite(valor) and valor > minimo


def _validar_backend_graphiti(bcfg, campo, fichero, errores):
    """Reglas propias de `type: "graphiti"` (T-01), sobre `bcfg["config"]`. El chequeo genérico
    de `backends.<id>` (type/enabled/config es-un-objeto) ya corrió antes de llamar aquí; esta
    función solo mira dentro de `config` y no repite esas comprobaciones."""
    config = bcfg.get("config")
    if not isinstance(config, dict):
        # gap #6: `config` ausente (o de tipo invalido, ya reportado como error generico de
        # `backends.<id>.config`) NO exime del chequeo de obligatoriedad con `enabled: true` —
        # antes, `{"type":"graphiti","enabled":true}` sin `config` pasaba en silencio.
        if bcfg.get("enabled") is True:
            campo_c = f"{campo}.config"
            errores.append(_error(
                "`endpoint` es obligatorio con el backend habilitado", fichero, f"{campo_c}.endpoint"))
            errores.append(_error(
                "`provider.llm` es obligatorio con el backend habilitado", fichero, f"{campo_c}.provider.llm"))
            errores.append(_error(
                "`mode` es obligatorio con el backend habilitado", fichero, f"{campo_c}.mode"))
        return
    campo_c = f"{campo}.config"

    for clave in config:
        if clave not in _GRAPHITI_CONFIG_CLAVES:
            errores.append(_error(
                f"clave desconocida `{clave}` en `config` de `type: \"graphiti\"`",
                fichero, f"{campo_c}.{clave}"))

    allow_remote_declarado = config.get("allow_remote")
    if "allow_remote" in config and not isinstance(allow_remote_declarado, bool):
        errores.append(_error("`allow_remote` debe ser booleano", fichero, f"{campo_c}.allow_remote"))
    # gap #14: leído por identidad estricta, nunca por truthiness — `"no"` (str, truthy en Python)
    # no puede colarse como si autorizara un endpoint remoto.
    allow_remote = allow_remote_declarado is True

    mode = config.get("mode")
    if mode is not None and mode not in GRAPHITI_MODE_VALORES:
        errores.append(_error(
            f"`mode` `{mode}` no es uno de {GRAPHITI_MODE_VALORES}", fichero, f"{campo_c}.mode"))

    endpoint = config.get("endpoint")
    if endpoint is not None:
        if not isinstance(endpoint, str) or not endpoint:
            errores.append(_error("`endpoint` debe ser una cadena no vacía", fichero, f"{campo_c}.endpoint"))
        elif not (endpoint.startswith("http://") or endpoint.startswith("https://")):
            errores.append(_error(
                "`endpoint` debe ser una URL http(s)", fichero, f"{campo_c}.endpoint"))
        elif not _url_parseable(endpoint):
            # gap #63: no se interpola `endpoint` -si no se puede ni parsear no hay forma segura
            # de mostrarlo sin arriesgar credenciales embebidas mal formadas.
            errores.append(_error(
                "`endpoint` no es una URL válida (no se puede interpretar)", fichero, f"{campo_c}.endpoint"))
        elif _url_con_userinfo(endpoint):
            # gap #43: userinfo (`usuario:token@host`) nunca se acepta, aunque el host sea local.
            errores.append(_error(
                "`endpoint` no puede contener credenciales embebidas (userinfo); usa "
                "`provider.api_key_env` para credenciales", fichero, f"{campo_c}.endpoint"))
        elif _url_con_direccion_prohibida(endpoint):
            # gap #75: prohibida SIEMPRE, tambien con `allow_remote: true` (misma regla que el
            # adaptador: `allow_remote` autoriza salir a redes remotas, no a la red de metadatos
            # del propio host, a `0.0.0.0`/`::` ni a prefijos de transicion IPv6 -gap #71-).
            errores.append(_error(
                f"`endpoint` `{endpoint}` apunta a una direccion prohibida SIEMPRE (metadatos de "
                "nube/link-local, no especificada o 6to4/Teredo), ni siquiera con "
                "`allow_remote: true`", fichero, f"{campo_c}.endpoint"))
        elif not allow_remote and not _endpoint_es_local(endpoint):
            errores.append(_error(
                f"`endpoint` `{endpoint}` no es local/privado; declara `allow_remote: true` "
                "para permitir un endpoint remoto (CA-09)", fichero, f"{campo_c}.endpoint"))

    # gap #70 (fix4): topes de RECURSOS del adaptador — enteros estrictos y mayores que 0.
    # `max_respuesta_kb` capa la lectura de CADA respuesta MCP (default 8192 KiB, 8 MiB);
    # `max_episodes` capa la ventana de `get_episodes` que barre `verify()`.
    for clave_tope, descripcion in (
            ("max_respuesta_kb", "tope de lectura de una respuesta MCP, en KiB"),
            ("max_episodes", "tope de la ventana de `get_episodes` de `verify()`")):
        valor_tope = config.get(clave_tope)
        if clave_tope in config and (isinstance(valor_tope, bool)
                                      or not isinstance(valor_tope, int) or valor_tope <= 0):
            errores.append(_error(
                f"`{clave_tope}` debe ser un entero mayor que 0 ({descripcion})",
                fichero, f"{campo_c}.{clave_tope}"))

    group_id = config.get("group_id")
    if "group_id" in config and not isinstance(group_id, str):
        errores.append(_error("`group_id` debe ser una cadena", fichero, f"{campo_c}.group_id"))
    elif isinstance(group_id, str) and not group_id.strip():
        # gap #3: sin default cableado (se deriva del slug del proyecto en `cargar_taxonomia`,
        # igual que `id_prefix`); una vez declarado (o derivado) NO puede ser cadena vacía.
        errores.append(_error("`group_id` no puede ser una cadena vacía", fichero, f"{campo_c}.group_id"))

    provider = config.get("provider")
    if provider is not None:
        if not isinstance(provider, dict):
            errores.append(_error("`provider` debe ser un objeto", fichero, f"{campo_c}.provider"))
        else:
            for clave in provider:
                if clave not in _GRAPHITI_PROVIDER_CLAVES:
                    errores.append(_error(
                        f"clave desconocida `{clave}` en `provider`", fichero, f"{campo_c}.provider.{clave}"))
            llm = provider.get("llm")
            if llm is None:
                errores.append(_error("`provider.llm` es obligatorio", fichero, f"{campo_c}.provider.llm"))
            elif llm not in GRAPHITI_PROVIDER_LLM_VALORES:
                errores.append(_error(
                    f"`provider.llm` `{llm}` no es uno de {GRAPHITI_PROVIDER_LLM_VALORES}",
                    fichero, f"{campo_c}.provider.llm"))
            elif llm != "none":
                # gap #37 (revisión Fase 2 intento 1): sin `provider.model` obligatorio,
                # `graphiti_providers.py` caía a un modelo CABLEADO en el código
                # (`qwen2.5:7b`/`gpt-4o-mini`/`claude-haiku`) contra CA-09 ("ningún modelo ni
                # endpoint tiene default cableado"); con `llm != "none"` el modelo es del proyecto.
                modelo = provider.get("model")
                if not isinstance(modelo, str) or not modelo.strip():
                    errores.append(_error(
                        "`provider.model` es obligatorio cuando `provider.llm` no es \"none\"",
                        fichero, f"{campo_c}.provider.model"))
            for clave in ("model", "embedder", "embedder_model", "base_url"):
                if clave in provider and not isinstance(provider[clave], str):
                    errores.append(_error(
                        f"`provider.{clave}` debe ser una cadena", fichero, f"{campo_c}.provider.{clave}"))
            api_key_env = provider.get("api_key_env")
            if api_key_env is not None:
                if not isinstance(api_key_env, str) or not _ENV_VAR_RE.match(api_key_env):
                    errores.append(_error(
                        "`provider.api_key_env` debe ser el NOMBRE de una variable de entorno "
                        "(nunca la credencial en sí, CA-09)", fichero, f"{campo_c}.provider.api_key_env"))

    entity_map = config.get("entity_map")
    if entity_map is not None:
        # T-01-fix2 gap #20 (parte schema, mutante M15): un valor cadena VACIA o solo blancos
        # (`""`, `"  "`) pasaba `isinstance(v, str)` y quedaba como tipo de entidad efectivo; el
        # adaptador Graphiti lo enviaria tal cual al servidor.
        if not isinstance(entity_map, dict) or not all(
                isinstance(k, str) and isinstance(v, str) and v.strip()
                for k, v in entity_map.items()):
            errores.append(_error(
                "`entity_map` debe ser un objeto {categoria: tipo_del_servidor} de cadenas no vacías",
                fichero, f"{campo_c}.entity_map"))

    timeout_ms = config.get("timeout_ms")
    if "timeout_ms" in config and not _numero_finito_mayor_que(timeout_ms, 0):
        # T-01-fix2 gap #19/#21: mismo guardarraíl que `health.timeout_ms` (finito, > 0).
        errores.append(_error(
            "`timeout_ms` debe ser un entero finito y mayor que 0", fichero, f"{campo_c}.timeout_ms"))

    concurrency = config.get("concurrency")
    if "concurrency" in config:
        if (isinstance(concurrency, bool) or not isinstance(concurrency, int)
                or concurrency < 1):
            # T-01-fix2 gap #19: consistente con `SEMAPHORE_LIMIT: 1` del stack de referencia
            # (docs/knowledge/gotchas del stack local Graphiti); entero, nunca bool, >= 1.
            errores.append(_error(
                "`concurrency` debe ser un entero mayor o igual que 1", fichero, f"{campo_c}.concurrency"))

    episode_body_max_kb = config.get("episode_body_max_kb")
    if "episode_body_max_kb" in config and not _numero_finito_mayor_que(episode_body_max_kb, 0):
        # Gap #64 (Minor): tope configurable, con aviso, del tamaño de `episode_body` que viaja
        # a `add_memory` (el arbitraje de #42 lo pedía); mismo guardarraíl que `timeout_ms`
        # (entero finito, nunca bool, > 0 — el default de 512 KiB lo aplica `graphiti.py` cuando
        # la clave no está declarada).
        errores.append(_error(
            "`episode_body_max_kb` debe ser un entero finito y mayor que 0",
            fichero, f"{campo_c}.episode_body_max_kb"))

    relations = config.get("relations")
    if relations is not None:
        if not isinstance(relations, list) or not all(
                isinstance(r, str) and r for r in relations):
            errores.append(_error(
                "`relations` debe ser una lista de cadenas no vacías", fichero, f"{campo_c}.relations"))

    router = config.get("router")
    if router is not None:
        if not isinstance(router, dict):
            errores.append(_error("`router` debe ser un objeto", fichero, f"{campo_c}.router"))
        else:
            for clave in router:
                if clave not in _GRAPHITI_ROUTER_CLAVES:
                    errores.append(_error(
                        f"clave desconocida `{clave}` en `router`", fichero, f"{campo_c}.router.{clave}"))
            if "default" in router and not isinstance(router["default"], str):
                errores.append(_error("`router.default` debe ser una cadena", fichero, f"{campo_c}.router.default"))
            intents = router.get("intents")
            if intents is not None:
                if not isinstance(intents, dict):
                    errores.append(_error(
                        "`router.intents` debe ser un objeto {intent: booleano}",
                        fichero, f"{campo_c}.router.intents"))
                else:
                    for intent, valor in intents.items():
                        if not isinstance(valor, bool):
                            errores.append(_error(
                                f"`router.intents.{intent}` debe ser booleano",
                                fichero, f"{campo_c}.router.intents.{intent}"))

    if "telemetria" in config and not isinstance(config["telemetria"], bool):
        errores.append(_error("`telemetria` debe ser booleano", fichero, f"{campo_c}.telemetria"))

    health = config.get("health")
    if health is not None:
        if not isinstance(health, dict):
            errores.append(_error("`health` debe ser un objeto", fichero, f"{campo_c}.health"))
        else:
            for clave in health:
                if clave not in _GRAPHITI_HEALTH_CLAVES:
                    errores.append(_error(
                        f"clave desconocida `{clave}` en `health`", fichero, f"{campo_c}.health.{clave}"))
            health_url = health.get("url")
            if "url" in health:
                if not isinstance(health_url, str) or not health_url:
                    errores.append(_error("`health.url` debe ser una cadena no vacía", fichero, f"{campo_c}.health.url"))
                elif not (health_url.startswith("http://") or health_url.startswith("https://")):
                    errores.append(_error(
                        "`health.url` debe ser una URL http(s)", fichero, f"{campo_c}.health.url"))
                elif not _url_parseable(health_url):
                    # gap #63: mismo guardarraíl que `endpoint`, sin interpolar la URL cruda.
                    errores.append(_error(
                        "`health.url` no es una URL válida (no se puede interpretar)",
                        fichero, f"{campo_c}.health.url"))
                elif _url_con_userinfo(health_url):
                    # gap #43: mismo guardarraíl que `endpoint`.
                    errores.append(_error(
                        "`health.url` no puede contener credenciales embebidas (userinfo); usa "
                        "`provider.api_key_env` para credenciales", fichero, f"{campo_c}.health.url"))
                elif _url_con_direccion_prohibida(health_url):
                    # gap #75: mismo guardarrail que `endpoint`, tambien con `allow_remote: true`.
                    errores.append(_error(
                        f"`health.url` `{health_url}` apunta a una direccion prohibida SIEMPRE "
                        "(metadatos de nube/link-local, no especificada o 6to4/Teredo), ni "
                        "siquiera con `allow_remote: true`", fichero, f"{campo_c}.health.url"))
                elif not allow_remote and not _endpoint_es_local(health_url):
                    # gap #7: mismo guardarraíl que `endpoint` (precedente `markdown_export.py`
                    # pasando `health_url` por `_host_permitido` antes de llamarlo).
                    errores.append(_error(
                        f"`health.url` `{health_url}` no es local/privado; declara "
                        "`allow_remote: true` para permitir un health remoto (CA-09)",
                        fichero, f"{campo_c}.health.url"))
            health_timeout_ms = health.get("timeout_ms")
            if health_timeout_ms is not None and not _numero_finito_mayor_que(health_timeout_ms, 0):
                # T-01-fix2 gap #21: `timeout_ms <= 0` con NaN/Infinity siempre da `False` (toda
                # comparación con NaN lo es), así que `float('nan')`/`float('inf')` colaban aquí.
                errores.append(_error(
                    "`health.timeout_ms` debe ser un entero finito y mayor que 0",
                    fichero, f"{campo_c}.health.timeout_ms"))

    if bcfg.get("enabled") is True:
        # gap #6: con el backend habilitado, `endpoint`, `provider.llm` y `mode` son obligatorios
        # (antes, `{"type":"graphiti","enabled":true}` sin `config`, o `config` sin ninguna de
        # estas claves, validaba en silencio y `knowledge-sync.py` entregaba `cfg = {}` al
        # adaptador).
        if not endpoint:
            errores.append(_error(
                "`endpoint` es obligatorio con el backend habilitado", fichero, f"{campo_c}.endpoint"))
        if provider is None:
            # `provider` presente sin `llm` ya se reportó arriba; aquí solo falta el caso
            # "provider ausente del todo".
            errores.append(_error(
                "`provider.llm` es obligatorio con el backend habilitado", fichero, f"{campo_c}.provider.llm"))
        if not mode:
            errores.append(_error(
                "`mode` es obligatorio con el backend habilitado", fichero, f"{campo_c}.mode"))


_FOLDER_UNIDAD_RE = re.compile(r"^[A-Za-z]:")


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


def default_taxonomy():
    """La plantilla por defecto del plugin, leída del disco si está disponible; si no, el
    respaldo embebido (mismo contenido). Nunca lanza (gap 14: una plantilla con encoding
    corrupto/truncado no debe tumbar el CLI ni `cargar_taxonomia`, cae al respaldo igual que un
    fichero ilegible o JSON invalido)."""
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        # ValueError cubre json.JSONDecodeError y UnicodeDecodeError (ambas subclases).
        return json.loads(json.dumps(_TAXONOMY_FALLBACK))


_SLUG_NO_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def _slug_kebab(nombre):
    """kebab-case determinista y minimo (minusculas, alfanumericos separados por un solo `-`,
    sin guiones al borde). Cadena vacia si `nombre` no aporta ningun caracter alfanumerico."""
    if not nombre:
        return ""
    return _SLUG_NO_ALNUM_RE.sub("-", nombre.lower()).strip("-")


def _graphiti_backends(config):
    """Todos los `(id, bcfg)` de `config["backends"]` cuyo `type` sea `"graphiti"` (T-01-fix2
    gap #17): antes, `_con_group_id_por_defecto` solo miraba la clave literal
    `backends.graphiti`, así que un backend declarado como `backends.graphiti_dev` o
    `backends.mi_graphiti` (mismo `type`, otra clave) nunca recibía `group_id` derivado."""
    backends = config.get("backends")
    if not isinstance(backends, dict):
        return []
    return [(bid, bcfg) for bid, bcfg in backends.items()
            if isinstance(bcfg, dict) and bcfg.get("type") == "graphiti"]


# --8<-- group_id por defecto COMPARTIDO (memoria de grafo, T-07-fix1) — REPLICADO LITERAL en agent-kits/shared/knowledge-schema.py y agent-kits/shared/knowledge-find.py
# Gap #97 (Critical, fix1 Fase 3): la derivacion del `group_id` por defecto (el slug Unicode del
# directorio del proyecto) la aplicaba SOLO el validador al cargar la taxonomia, asi que el router
# de `knowledge-find.py` -que NO carga el validador, para que ningun hook alcance codigo con
# capacidad de red- servia al adaptador la config CRUDA; con la plantilla de fabrica (que no trae
# `group_id`) el backend cortaba con «sin group_id» y la consulta devolvia 0 en la configuracion
# NOMINAL. La regla vive aqui, una sola vez, y sin un solo import de red.
_SLUG_UNICODE_SEP_RE = re.compile(r"[\W_]+", re.UNICODE)


def _slug_unicode(nombre):
    """Slug consciente de Unicode (NFKC + minusculas + separador de restos no alfanumericos),
    para `group_id` (T-01-fix2 gap #23). A diferencia de un slug solo ASCII, conserva
    letras/digitos no latinos (acentos, CJK, cirilico...) en vez de descartarlos todos y caer a
    cadena vacia. Sin fallback fijo a proposito: ver `_group_id_por_defecto`."""
    if not nombre:
        return ""
    normalizado = unicodedata.normalize("NFKC", nombre).lower()
    return _SLUG_UNICODE_SEP_RE.sub("-", normalizado).strip("-")


def _group_id_por_defecto(root):
    """Slug Unicode del directorio del proyecto (`root=None` -> cwd real), o `""` si el nombre no
    aporta ningun caracter alfanumerico. SIN fallback fijo: dos instalaciones con nombres "raros"
    no pueden acabar compartiendo grupo remoto (fusionaria su memoria)."""
    return _slug_unicode(os.path.basename(os.path.abspath(root if root is not None else ".")))


def _config_con_group_id(cfg, root):
    """Config EFECTIVA de un backend: la declarada MAS el `group_id` derivado si no lo trae (o lo
    trae vacio). Nunca pisa un `group_id` explicito."""
    efectiva = dict(cfg or {})
    declarado = efectiva.get("group_id")
    if not (isinstance(declarado, str) and declarado.strip()):
        derivado = _group_id_por_defecto(root)
        if derivado:
            efectiva["group_id"] = derivado
    return efectiva
# --8<-- fin group_id por defecto COMPARTIDO


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


def _con_group_id_por_defecto(config, root):
    """Para CADA backend de `type: "graphiti"` (T-01-fix2 gap #17: por `type`, no por la clave
    literal `graphiti` — ver `_graphiti_backends`) que no declare `group_id` (o lo declare
    vacío), lo rellena con el slug Unicode del directorio del proyecto (gap #23:
    `_slug_unicode`, no `_slug_kebab` — conserva nombres no ASCII en vez de vaciarlos). No pisa
    un `group_id` explícito y no vacío. `root=None` usa el cwd real, igual que
    `_con_id_prefix_por_defecto`.

    A propósito SIN fallback `"ca"` aquí (a diferencia de `_con_id_prefix_por_defecto`): un
    directorio sin ningún carácter alfanumérico (p. ej. solo símbolos) produciría un slug vacío
    y, si cayera a `"ca"` en silencio, dos instalaciones distintas con nombres "raros" acabarían
    compartiendo el MISMO `group_id` de Graphiti — mezclando su memoria de proyecto sin que nadie
    lo pidiera; exactamente la clase de bug que el gap #3 ya corrigió para nombres ASCII
    corrientes. `id_prefix` SÍ mantiene el fallback `"ca"` (no se toca aquí, rompería
    `test_id_prefix_*`): un `id_prefix` colisionado es cosmético (prefijo de fichero local); un
    `group_id` colisionado fusiona datos de otro proyecto en el grafo de conocimiento remoto. Si
    el slug deriva vacío con el backend habilitado, `_errores_group_id_tras_derivar` levanta un
    error explícito pidiendo declarar `group_id` a mano, en vez de fallar en silencio."""
    if not isinstance(config, dict):
        return config
    for _bid, graphiti_bcfg in _graphiti_backends(config):
        graphiti_config = graphiti_bcfg.get("config")
        if not isinstance(graphiti_config, dict):
            continue
        # Gap #132 (Minor, fix2 Fase 3; salvedad de #97): la derivacion la hace la COPIA DECLARADA
        # `_config_con_group_id` (la misma que usa el router en `knowledge-find.py`), no un
        # predicado propio. Con el `truthy` de antes, `group_id: "   "` se conservaba aqui y el
        # router SI derivaba el slug: dos respuestas distintas para la misma config. La copia
        # nunca pisa un `group_id` explicito y no vacio, asi que asignar su resultado es seguro.
        derivado = _config_con_group_id(graphiti_config, root).get("group_id")
        if derivado:
            graphiti_config["group_id"] = derivado
    return config


def _errores_group_id_tras_derivar(config, ruta):
    """Tras `_con_group_id_por_defecto` (T-01-fix2 gaps #17/#23): con el backend graphiti
    habilitado, `group_id` es obligatorio — si el directorio del proyecto no aportó ningún
    carácter alfanumérico y no se derivó nada, exige declararlo explícito en vez de dejarlo
    ausente en silencio (o caer a un fallback fijo que fusionaría proyectos distintos, ver nota
    en `_con_group_id_por_defecto`). Debe invocarse DESPUÉS de la derivación, no dentro de
    `validar()`: `validar()` corre antes de que `cargar_taxonomia` derive nada."""
    errores = []
    for bid, bcfg in _graphiti_backends(config):
        if bcfg.get("enabled") is not True:
            continue
        graphiti_config = bcfg.get("config")
        group_id = graphiti_config.get("group_id") if isinstance(graphiti_config, dict) else None
        if not isinstance(group_id, str) or not group_id.strip():
            errores.append(_error(
                "`group_id` es obligatorio con el backend habilitado y no se pudo derivar del "
                "directorio del proyecto (sin caracteres alfanuméricos); declara `group_id` "
                "explícitamente", ruta, f"backends.{bid}.config.group_id"))
    return errores


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
            elif bcfg.get("type") == "graphiti":
                # gap #1: cualquier clave fuera de {type, enabled, config} a nivel de
                # `backends.graphiti` (p. ej. el `endpoint` PLANO del ejemplo antiguo de
                # design.md) es error — antes se ignoraba en silencio.
                for clave in bcfg:
                    if clave not in _BACKEND_CLAVES:
                        errores.append(_error(
                            f"backend `{bid}`: clave desconocida `{clave}` (¿pertenece a `config`?)",
                            fichero, f"{campo}.{clave}"))
                _validar_backend_graphiti(bcfg, campo, fichero, errores)

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
                        if valor not in ROUTING_VALORES:
                            errores.append(_error(
                                f"{campo_r} debe ser true, false o \"summary\"", fichero, campo_r))
            # Sin `routing` declarado: fail-closed, no es un error de esquema (CA-09), solo
            # significa que la categoría no exporta a ningún backend.

    return errores


def cargar_taxonomia(root=None, fichero=None):
    """(config, origen, ruta_o_None, errores). `origen` = "proyecto" | "default".
    Si `fichero` se pasa explícito, se valida ese; si no, se busca
    `<root>/.claude/knowledge-services/taxonomy.json` — `root=None` (igual que el docstring
    siempre prometió) busca desde el cwd, no se salta la busqueda (gap 12: antes, `root=None`
    devolvia el default SIN mirar si el cwd tenia un `taxonomy.json` de proyecto). Sin fichero de
    proyecto → la plantilla por defecto (CA-01/CA-09), sin error. Con fichero de proyecto
    inválido → se devuelve igualmente (para que el llamador decida) junto con los errores. En
    ambos casos, si `config` no declara `id_prefix`, se rellena con el slug del `root` (gap 5); lo
    mismo para `backends.graphiti.config.group_id` (gap #3 de la revisión de la Fase 1)."""
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
        errores = validar(config, ruta)
        _con_id_prefix_por_defecto(config, root)
        _con_group_id_por_defecto(config, root)
        # T-01-fix2 gaps #17/#23: `group_id` obligatorio con el backend habilitado se comprueba
        # DESPUÉS de derivar (validar() corre antes de que exista el slug derivado).
        errores = errores + _errores_group_id_tras_derivar(config, ruta)
        return config, "proyecto", ruta, errores
    config = default_taxonomy()
    _con_id_prefix_por_defecto(config, root)
    _con_group_id_por_defecto(config, root)
    errores = _errores_group_id_tras_derivar(config, None)
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
