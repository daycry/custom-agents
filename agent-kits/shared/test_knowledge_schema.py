import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    spec = importlib.util.spec_from_file_location("knowledge_schema", os.path.join(HERE, "knowledge-schema.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["knowledge_schema"] = mod
    spec.loader.exec_module(mod)
    return mod


ks = _load()


def _valida(**over):
    cfg = json.loads(json.dumps(ks._TAXONOMY_FALLBACK))
    cfg.update(over)
    return cfg


# ------------------------------------------------------------------ estructura básica

def test_default_template_es_valido():
    assert ks.validar(ks.default_taxonomy(), "template") == []


def test_default_fallback_es_valido():
    assert ks.validar(json.loads(json.dumps(ks._TAXONOMY_FALLBACK)), "fallback") == []


def test_default_fallback_coincide_con_el_template():
    """T-01-fix1 (lint_plugin.py, ADR-016): el respaldo embebido tiene que ser el MISMO contenido
    que `templates/taxonomy.json`, no solo cada uno valido por su lado — sin este test, el
    respaldo podia divergir del canonico en SILENCIO (aqui detecta que faltaba
    `backends.kwipu.config.health`)."""
    with open(os.path.join(HERE, "templates", "taxonomy.json"), encoding="utf-8") as f:
        plantilla = json.load(f)
    respaldo = json.loads(json.dumps(ks._TAXONOMY_FALLBACK))
    assert respaldo == plantilla, (
        "_TAXONOMY_FALLBACK (knowledge-schema.py) diverge de templates/taxonomy.json: "
        "actualiza el respaldo para que refleje el mismo contenido")


def test_falta_version():
    cfg = _valida()
    del cfg["version"]
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "version" for e in errores)


def test_version_no_soportada():
    cfg = _valida(version=99)
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "version" for e in errores)


def test_categories_vacio_es_invalido():
    cfg = _valida(categories=[])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "categories" for e in errores)


def test_key_duplicada():
    cfg = _valida(categories=[
        {"key": "DECISION", "folder": "adr", "min_evidence": "observation", "routing": {}},
        {"key": "DECISION", "folder": "adr2", "min_evidence": "observation", "routing": {}},
    ])
    errores = ks.validar(cfg, "t.json")
    assert any("key" in e["campo"] and "duplicada" in e["mensaje"] for e in errores)


def test_min_evidence_fuera_de_evidence_levels():
    cfg = _valida(categories=[
        {"key": "X", "folder": "x", "min_evidence": "nivel-inventado", "routing": {}},
    ])
    errores = ks.validar(cfg, "t.json")
    assert any("min_evidence" in e["campo"] for e in errores)


# ------------------------------------------------------------------ routing fail-closed (CA-11)

def test_routing_a_backend_no_declarado_falla():
    cfg = _valida(
        backends={"kwipu": {"type": "markdown-export"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation",
                     "routing": {"graphiti": True}}],
    )
    errores = ks.validar(cfg, "t.json")
    assert any("graphiti" in e["mensaje"] and "no declarado" in e["mensaje"] for e in errores)
    assert any(e["campo"] == "categories[0].routing.graphiti" for e in errores)


def test_routing_a_backend_declarado_es_valido():
    cfg = _valida(
        backends={"kwipu": {"type": "markdown-export"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation",
                     "routing": {"kwipu": True}}],
    )
    assert ks.validar(cfg, "t.json") == []


def test_routing_valor_invalido():
    cfg = _valida(
        backends={"kwipu": {"type": "markdown-export"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation",
                     "routing": {"kwipu": "todo"}}],
    )
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "categories[0].routing.kwipu" for e in errores)


def test_categoria_sin_routing_no_es_error_pero_no_exporta():
    cfg = _valida(
        backends={"kwipu": {"type": "markdown-export"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation"}],
    )
    assert ks.validar(cfg, "t.json") == []
    assert ks.categorias_por_backend(cfg, "kwipu") == []


# ------------------------------------------------------------------ backends

def test_backend_sin_type_falla():
    cfg = _valida(backends={"kwipu": {}})
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.kwipu.type" for e in errores)


def test_backend_enabled_no_booleano():
    cfg = _valida(backends={"kwipu": {"type": "markdown-export", "enabled": "si"}})
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.kwipu.enabled" for e in errores)


# ------------------------------------------------------------------ backends.graphiti (T-01, CA-09/CA-10/CA-12/CA-13)

def _graphiti_config(**over):
    cfg = {
        "mode": "shadow",
        "endpoint": "http://127.0.0.1:8001/mcp",
        "group_id": "knowledge-graphs",
        "allow_remote": False,
        "provider": {"llm": "ollama", "model": "qwen2.5:7b", "base_url": "http://127.0.0.1:11434",
                     "embedder": "ollama", "embedder_model": "nomic-embed-text"},
        "entity_map": {"PATTERN": "Document"},
        "relations": ["MITIGATES", "APPLIES_TO"],
        "router": {"intents": {"temporal": True, "relacional": False, "evidencia": False}},
        "telemetria": False,
        "health": {"url": "http://127.0.0.1:8001/health", "timeout_ms": 3000},
    }
    cfg.update(over)
    return cfg


def _con_graphiti(config):
    cfg = _valida()
    cfg["backends"]["graphiti"] = {"type": "graphiti", "enabled": True, "config": config}
    return cfg


def test_graphiti_config_valida_no_da_error():
    errores = ks.validar(_con_graphiti(_graphiti_config()), "t.json")
    assert errores == []


def test_graphiti_mode_invalido():
    cfg = _con_graphiti(_graphiti_config(mode="lectura-total"))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.mode" for e in errores)


def test_graphiti_endpoint_no_local_sin_allow_remote_falla():
    cfg = _con_graphiti(_graphiti_config(endpoint="http://ejemplo-remoto.com/mcp", allow_remote=False))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.endpoint" for e in errores)


def test_graphiti_endpoint_no_local_con_allow_remote_es_valido():
    cfg = _con_graphiti(_graphiti_config(endpoint="http://ejemplo-remoto.com/mcp", allow_remote=True))
    assert ks.validar(cfg, "t.json") == []


def test_graphiti_provider_llm_invalido():
    cfg = _con_graphiti(_graphiti_config(provider={"llm": "gemini"}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.provider.llm" for e in errores)


def test_graphiti_provider_none_no_exige_modelo():
    cfg = _con_graphiti(_graphiti_config(provider={"llm": "none"}))
    assert ks.validar(cfg, "t.json") == []


def test_graphiti_provider_api_key_no_puede_ser_un_secreto_inline():
    """CA-09: las credenciales viajan por NOMBRE de variable de entorno, nunca un valor literal
    largo (heurística: un `api_key_env` con espacios no es un nombre de variable válido)."""
    cfg = _con_graphiti(_graphiti_config(provider={"llm": "openai", "api_key_env": "sk-abc 123 real key"}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.provider.api_key_env" for e in errores)


def test_graphiti_provider_api_key_env_como_nombre_de_variable_es_valido():
    cfg = _con_graphiti(_graphiti_config(provider={"llm": "openai", "api_key_env": "OPENAI_API_KEY"}))
    assert ks.validar(cfg, "t.json") == []


def test_graphiti_router_intents_valor_no_booleano():
    cfg = _con_graphiti(_graphiti_config(router={"intents": {"temporal": "si"}}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.router.intents.temporal" for e in errores)


def test_graphiti_relations_no_lista_de_cadenas():
    cfg = _con_graphiti(_graphiti_config(relations=[1, 2]))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.relations" for e in errores)


def test_graphiti_entity_map_no_es_objeto_de_cadenas():
    cfg = _con_graphiti(_graphiti_config(entity_map={"PATTERN": 1}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.entity_map" for e in errores)


def test_graphiti_health_timeout_ms_no_numerico():
    cfg = _con_graphiti(_graphiti_config(health={"url": "http://127.0.0.1:8001/health", "timeout_ms": "rapido"}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.health.timeout_ms" for e in errores)


def test_graphiti_telemetria_no_booleana():
    cfg = _con_graphiti(_graphiti_config(telemetria="no"))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.telemetria" for e in errores)


def test_graphiti_allow_remote_no_booleano():
    cfg = _con_graphiti(_graphiti_config(allow_remote="no"))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.allow_remote" for e in errores)


# ------------------------------------------------------------------ T-01-fix1: revision de dos lentes, Fase 1 intento 1

def test_graphiti_clave_desconocida_a_nivel_de_backend_falla():
    """Gap #1: el ejemplo PLANO antiguo (`endpoint` fuera de `config`) tiene que dar error, no
    pasar en silencio."""
    cfg = _valida()
    cfg["backends"]["graphiti"] = {
        "type": "graphiti", "enabled": True,
        "endpoint": "http://evil.com/mcp", "api_key": "sk-secreto-inline",
        "config": _graphiti_config(),
    }
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.endpoint" for e in errores)
    assert any(e["campo"] == "backends.graphiti.api_key" for e in errores)


def test_graphiti_clave_desconocida_en_config_falla():
    cfg = _con_graphiti(_graphiti_config(api_key="sk-secreto-inline"))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.api_key" for e in errores)


def test_graphiti_clave_desconocida_en_provider_falla():
    cfg = _con_graphiti(_graphiti_config(provider={"llm": "ollama", "modelo": "qwen2.5:7b"}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.provider.modelo" for e in errores)


def test_graphiti_clave_desconocida_en_router_falla():
    cfg = _con_graphiti(_graphiti_config(router={"intents": {"temporal": True}, "modelo": "gpt-4"}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.router.modelo" for e in errores)


def test_graphiti_clave_desconocida_en_health_falla():
    cfg = _con_graphiti(_graphiti_config(health={"url": "http://127.0.0.1:8001/health", "puerto": 8001}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.health.puerto" for e in errores)


def test_group_id_sin_default_cableado_en_template():
    """Gap #3: ni la plantilla ni el respaldo fijan `group_id` a `knowledge-graphs` (el grupo del
    stack de referencia); dos consumidores en la misma maquina no pueden compartir grupo por
    omision."""
    tpl = ks.default_taxonomy()
    assert "group_id" not in tpl["backends"]["graphiti"]["config"]
    assert "group_id" not in ks._TAXONOMY_FALLBACK["backends"]["graphiti"]["config"]
    assert ks.validar(tpl, "template") == []


def test_group_id_se_deriva_del_slug_del_proyecto(tmp_path):
    root = tmp_path / "Mi Proyecto Graphiti"
    root.mkdir()
    config, origen, _ruta, errores = ks.cargar_taxonomia(root=str(root))
    assert origen == "default"
    assert errores == []
    assert config["backends"]["graphiti"]["config"]["group_id"] == "mi-proyecto-graphiti"


def test_group_id_explicito_no_se_pisa(tmp_path):
    proyecto = tmp_path / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    cfg = _con_graphiti(_graphiti_config(group_id="grupo-explicito"))
    (proyecto / "taxonomy.json").write_text(json.dumps(cfg), encoding="utf-8")
    config, _origen, _ruta, _errores = ks.cargar_taxonomia(root=str(tmp_path))
    assert config["backends"]["graphiti"]["config"]["group_id"] == "grupo-explicito"


def test_group_id_vacio_es_invalido():
    cfg = _con_graphiti(_graphiti_config(group_id=""))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.group_id" for e in errores)


def test_graphiti_habilitado_sin_config_falla_en_endpoint_provider_y_mode():
    """Gap #6: `{"type":"graphiti","enabled":true}` sin `config` ya no valida en silencio."""
    cfg = _valida()
    cfg["backends"]["graphiti"] = {"type": "graphiti", "enabled": True}
    errores = ks.validar(cfg, "t.json")
    campos = {e["campo"] for e in errores}
    assert "backends.graphiti.config.endpoint" in campos
    assert "backends.graphiti.config.provider.llm" in campos
    assert "backends.graphiti.config.mode" in campos


def test_graphiti_habilitado_config_vacia_falla_en_endpoint_provider_y_mode():
    cfg = _valida()
    cfg["backends"]["graphiti"] = {"type": "graphiti", "enabled": True, "config": {}}
    errores = ks.validar(cfg, "t.json")
    campos = {e["campo"] for e in errores}
    assert "backends.graphiti.config.endpoint" in campos
    assert "backends.graphiti.config.provider.llm" in campos
    assert "backends.graphiti.config.mode" in campos


def test_graphiti_deshabilitado_sin_config_no_exige_nada():
    cfg = _valida()
    cfg["backends"]["graphiti"] = {"type": "graphiti", "enabled": False}
    assert ks.validar(cfg, "t.json") == []


def test_graphiti_health_url_remota_publica_sin_allow_remote_falla():
    """Gap #7: `health.url` pasa por el MISMO guardarraíl que `endpoint`."""
    cfg = _con_graphiti(_graphiti_config(health={"url": "http://evil.com/health", "timeout_ms": 3000}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.health.url" for e in errores)


def test_graphiti_health_url_remota_con_allow_remote_es_valida():
    cfg = _con_graphiti(_graphiti_config(
        allow_remote=True, endpoint="http://ejemplo-remoto.com/mcp",
        health={"url": "http://ejemplo-remoto.com/health", "timeout_ms": 3000}))
    assert ks.validar(cfg, "t.json") == []


def test_graphiti_health_timeout_ms_negativo_o_cero_falla():
    """Gap #11."""
    for valor in (-5, 0):
        cfg = _con_graphiti(_graphiti_config(health={"url": "http://127.0.0.1:8001/health", "timeout_ms": valor}))
        errores = ks.validar(cfg, "t.json")
        assert any(e["campo"] == "backends.graphiti.config.health.timeout_ms" for e in errores), valor


def test_graphiti_host_local_con_sufijo_docker_es_valido():
    """Gap #15: mismo criterio de hosts locales que el adaptador Kwipu (`host.docker.internal`,
    sufijos `.test`/`.local`/`.internal`), no solo loopback/IP privada literal."""
    cfg = _con_graphiti(_graphiti_config(
        endpoint="http://host.docker.internal:8001/mcp", allow_remote=False,
        health={"url": "http://mi-graphiti.test/health", "timeout_ms": 3000}))
    assert ks.validar(cfg, "t.json") == []


# ------------------------------------------------------------------ mutantes M9/M10/M12 (gap #13)

def test_graphiti_endpoint_host_local_por_subcadena_falla_m9():
    """M9: `"localhost" in host` sobrevivia — `localhost.evil.com` NO es local."""
    cfg = _con_graphiti(_graphiti_config(endpoint="http://localhost.evil.com/mcp", allow_remote=False))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.endpoint" for e in errores)


def test_graphiti_endpoint_ip_publica_literal_falla_m10():
    """M10: cualquier IP literal se aceptaba — una IP publica (`8.8.8.8`) sigue exigiendo
    `allow_remote: true`."""
    cfg = _con_graphiti(_graphiti_config(endpoint="http://8.8.8.8/mcp", allow_remote=False))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.endpoint" for e in errores)


def test_graphiti_provider_vacio_falla_m12():
    """M12: `provider: {}` (sin `llm`) tiene que fallar."""
    cfg = _con_graphiti(_graphiti_config(provider={}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.provider.llm" for e in errores)


# ------------------------------------------------------------------ gap #14: allow_remote estricto, relations sin vacios

def test_graphiti_allow_remote_string_no_autoriza_endpoint_remoto():
    """Gap #14: `allow_remote: "no"` (string, truthy en Python) NO puede colarse como si
    autorizara un endpoint remoto."""
    cfg = _con_graphiti(_graphiti_config(endpoint="http://ejemplo-remoto.com/mcp", allow_remote="no"))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.allow_remote" for e in errores)
    assert any(e["campo"] == "backends.graphiti.config.endpoint" for e in errores)


def test_graphiti_relations_con_cadena_vacia_falla():
    cfg = _con_graphiti(_graphiti_config(relations=["MITIGATES", ""]))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.relations" for e in errores)


# --------------------------------------------- T-01-fix2 gap #20: entity_map con valor vacio (M15)

def test_graphiti_entity_map_valor_vacio_falla_m15():
    cfg = _con_graphiti(_graphiti_config(entity_map={"PATTERN": ""}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.entity_map" for e in errores)


def test_graphiti_entity_map_valor_blanco_falla():
    cfg = _con_graphiti(_graphiti_config(entity_map={"PATTERN": "   "}))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.entity_map" for e in errores)


# --------------------------------------------- T-01-fix2 gap #19: timeout_ms/concurrency de config

def test_graphiti_config_timeout_ms_valido_no_da_error():
    cfg = _con_graphiti(_graphiti_config(timeout_ms=3000))
    assert ks.validar(cfg, "t.json") == []


def test_graphiti_config_timeout_ms_no_numerico_falla():
    cfg = _con_graphiti(_graphiti_config(timeout_ms="rapido"))
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.graphiti.config.timeout_ms" for e in errores)


def test_graphiti_config_timeout_ms_negativo_o_cero_falla():
    for valor in (-5, 0):
        cfg = _con_graphiti(_graphiti_config(timeout_ms=valor))
        errores = ks.validar(cfg, "t.json")
        assert any(e["campo"] == "backends.graphiti.config.timeout_ms" for e in errores), valor


def test_graphiti_config_concurrency_valido_no_da_error():
    cfg = _con_graphiti(_graphiti_config(concurrency=1))
    assert ks.validar(cfg, "t.json") == []


def test_graphiti_config_concurrency_invalido_falla():
    for valor in (0, -1, 1.5, "1", True):
        cfg = _con_graphiti(_graphiti_config(concurrency=valor))
        errores = ks.validar(cfg, "t.json")
        assert any(e["campo"] == "backends.graphiti.config.concurrency" for e in errores), valor


def test_template_declara_timeout_ms_y_concurrency_por_defecto():
    tpl = ks.default_taxonomy()
    graphiti_cfg = tpl["backends"]["graphiti"]["config"]
    assert graphiti_cfg["timeout_ms"] == 3000
    assert graphiti_cfg["concurrency"] == 1
    assert ks.validar(tpl, "template") == []


# ------------------------------- T-01-fix2 gap #21: finitos (NaN/Infinity) en timeout_ms/concurrency

def test_graphiti_health_timeout_ms_no_finito_falla():
    for valor in (float("nan"), float("inf"), float("-inf"), 1e-09):
        cfg = _con_graphiti(_graphiti_config(
            health={"url": "http://127.0.0.1:8001/health", "timeout_ms": valor}))
        errores = ks.validar(cfg, "t.json")
        assert any(e["campo"] == "backends.graphiti.config.health.timeout_ms" for e in errores), valor


def test_graphiti_config_timeout_ms_no_finito_falla():
    for valor in (float("nan"), float("inf"), 1e-09):
        cfg = _con_graphiti(_graphiti_config(timeout_ms=valor))
        errores = ks.validar(cfg, "t.json")
        assert any(e["campo"] == "backends.graphiti.config.timeout_ms" for e in errores), valor


# ---------------------------------------------- T-01-fix2 gap #17: group_id derivado por `type`

def test_con_group_id_por_defecto_deriva_por_type_no_por_clave_literal():
    """Mutante M14: un backend `graphiti` con un ID DISTINTO de la clave literal `graphiti`
    también recibe su `group_id` derivado — antes, `_con_group_id_por_defecto` solo miraba
    `backends['graphiti']`, ignorando cualquier otro id declarado con `type: graphiti`."""
    config = _valida()
    graphiti_config = _graphiti_config()
    del graphiti_config["group_id"]
    config["backends"] = {"mi-grafo": {"type": "graphiti", "enabled": True, "config": graphiti_config}}
    resultado = ks._con_group_id_por_defecto(config, "/tmp/mi-proyecto-x")
    assert resultado["backends"]["mi-grafo"]["config"]["group_id"] == "mi-proyecto-x"


def test_group_id_obligatorio_tras_derivar_si_directorio_sin_alfanumericos(tmp_path):
    """Mutante M16: `group_id` faltante con `enabled: true` no puede validar en silencio — si el
    slug del directorio del proyecto queda vacío (sin caracteres alfanuméricos), es un error
    explícito en vez de un `group_id` ausente que T-04 resolvería cayendo al grupo por defecto del
    cliente MCP (justo lo que el gap #3 original quería impedir)."""
    root = tmp_path / "___"
    proyecto = root / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    cfg = _con_graphiti(_graphiti_config())
    del cfg["backends"]["graphiti"]["config"]["group_id"]
    (proyecto / "taxonomy.json").write_text(json.dumps(cfg), encoding="utf-8")
    config, origen, _ruta, errores = ks.cargar_taxonomia(root=str(root))
    assert origen == "proyecto"
    assert "group_id" not in config["backends"]["graphiti"]["config"]
    assert any("group_id" in e["campo"] for e in errores)


def test_group_id_no_obligatorio_tras_derivar_si_backend_deshabilitado(tmp_path):
    root = tmp_path / "___"
    proyecto = root / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    cfg = _con_graphiti(_graphiti_config())
    cfg["backends"]["graphiti"]["enabled"] = False
    del cfg["backends"]["graphiti"]["config"]["group_id"]
    (proyecto / "taxonomy.json").write_text(json.dumps(cfg), encoding="utf-8")
    config, _origen, _ruta, errores = ks.cargar_taxonomia(root=str(root))
    assert not any("group_id" in e["campo"] for e in errores)


# --------------------------------------------- T-01-fix2 gap #23: slug Unicode para group_id

def test_group_id_se_deriva_con_slug_unicode_no_cae_a_ca(tmp_path):
    root = tmp_path / "日本"
    root.mkdir()
    config, origen, _ruta, errores = ks.cargar_taxonomia(root=str(root))
    assert origen == "default"
    assert errores == []
    assert config["backends"]["graphiti"]["config"]["group_id"] == "日本"
    assert config["backends"]["graphiti"]["config"]["group_id"] != "ca"


def test_group_id_se_deriva_con_slug_unicode_acentos(tmp_path):
    root = tmp_path / "áéí"
    root.mkdir()
    config, _origen, _ruta, _errores = ks.cargar_taxonomia(root=str(root))
    assert config["backends"]["graphiti"]["config"]["group_id"] == "áéí"


def test_slug_unicode_normaliza():
    assert ks._slug_unicode("Mi Proyecto_X!!") == "mi-proyecto-x"
    assert ks._slug_unicode("") == ""
    assert ks._slug_unicode("---") == ""
    assert ks._slug_unicode("日本") == "日本"


def test_template_por_defecto_declara_graphiti_deshabilitado():
    """Regla del ledger: la plantilla gana el backend `graphiti` con `enabled: false` (opt-in)."""
    tpl = ks.default_taxonomy()
    assert tpl["backends"]["graphiti"]["type"] == "graphiti"
    assert tpl["backends"]["graphiti"]["enabled"] is False
    assert ks.validar(tpl, "template") == []


# ------------------------------------------------------------------ estado/tag inválidos (CA-01, CA-13)

def test_utility_scoring_no_booleano():
    cfg = _valida(utility_scoring="si")
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "utility_scoring" for e in errores)


def test_denylist_no_lista_de_cadenas():
    cfg = _valida(denylist=[1, 2, 3])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "denylist" for e in errores)


def test_contenido_no_es_objeto():
    errores = ks.validar([1, 2, 3], "t.json")
    assert errores and errores[0]["fichero"] == "t.json"


# ------------------------------------------------------------------ cargar_taxonomia (CA-01/CA-09)

def test_cargar_taxonomia_sin_fichero_usa_default(tmp_path):
    config, origen, ruta, errores = ks.cargar_taxonomia(root=str(tmp_path))
    assert origen == "default"
    assert ruta is None
    assert errores == []
    assert config["categories"]


def test_cargar_taxonomia_con_fichero_de_proyecto(tmp_path):
    proyecto = tmp_path / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    cfg = _valida(id_prefix="mr")
    (proyecto / "taxonomy.json").write_text(json.dumps(cfg), encoding="utf-8")
    config, origen, ruta, errores = ks.cargar_taxonomia(root=str(tmp_path))
    assert origen == "proyecto"
    assert ruta is not None
    assert errores == []
    assert config["id_prefix"] == "mr"


def test_cargar_taxonomia_json_invalido(tmp_path):
    proyecto = tmp_path / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    (proyecto / "taxonomy.json").write_text("{ esto no es json", encoding="utf-8")
    config, origen, ruta, errores = ks.cargar_taxonomia(root=str(tmp_path))
    assert origen == "proyecto"
    assert errores and "JSON ilegible" in errores[0]["mensaje"]


# ------------------------------------------------------------------ CLI

def test_cli_default_exit_0():
    assert ks.main(["--default"]) == 0


def test_cli_fichero_invalido_exit_1(tmp_path):
    p = tmp_path / "taxonomy.json"
    p.write_text(json.dumps({"version": 1, "categories": []}), encoding="utf-8")
    assert ks.main([str(p)]) == 1


def test_cli_fichero_inexistente_exit_2(tmp_path):
    assert ks.main([str(tmp_path / "no-existe.json")]) == 2


def test_cli_sin_argumentos_exit_2():
    assert ks.main([]) == 2


def test_cli_fichero_con_encoding_invalido_exit_2(tmp_path):
    """Gap 15: `UnicodeDecodeError` (fichero UTF-16, leido como utf-8) daba traceback en vez del
    exit 2 documentado."""
    p = tmp_path / "taxonomy.json"
    p.write_bytes("{\"version\": 1}".encode("utf-16"))
    assert ks.main([str(p)]) == 2


def test_cli_fichero_con_bom_utf8_exit_0(tmp_path):
    """Gap 39 (Important, revision intento 3, fix4): el CLI `knowledge-schema.py <ruta>` abria con
    `encoding="utf-8"` (sin `-sig`) mientras `cargar_taxonomia` ya tolera el BOM UTF-8 desde el
    gap 27 — el MISMO `taxonomy.json` con BOM pasaba por `cargar_taxonomia` (fichero de proyecto)
    pero fallaba como "JSON ilegible" por el CLI explicito. Tras fix4 ambos caminos comparten UN
    solo lector (`cargar_taxonomia(fichero=...)`)."""
    p = tmp_path / "taxonomy.json"
    cfg = _valida(id_prefix="mr")
    p.write_bytes(json.dumps(cfg).encode("utf-8-sig"))
    assert ks.main([str(p)]) == 0


def test_cli_ruta_es_directorio_exit_2(tmp_path):
    """Gap 15: TOCTOU — `os.path.isfile` decia que existia y `open()` fallaba con `OSError`
    (`IsADirectoryError`/`PermissionError` segun plataforma) sin capturar."""
    d = tmp_path / "no-es-un-fichero"
    d.mkdir()
    assert ks.main([str(d)]) == 2


# ------------------------------------------------------------------ id_prefix por defecto (gap 5)

def test_id_prefix_por_defecto_es_el_slug_del_directorio_raiz(tmp_path):
    root = tmp_path / "Mi Proyecto X"
    root.mkdir()
    config, origen, _ruta, errores = ks.cargar_taxonomia(root=str(root))
    assert origen == "default"
    assert errores == []
    assert config["id_prefix"] == "mi-proyecto-x"


def test_id_prefix_explicito_del_proyecto_no_se_pisa(tmp_path):
    proyecto = tmp_path / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    cfg = _valida(id_prefix="mr")
    (proyecto / "taxonomy.json").write_text(json.dumps(cfg), encoding="utf-8")
    config, _origen, _ruta, _errores = ks.cargar_taxonomia(root=str(tmp_path))
    assert config["id_prefix"] == "mr"


def test_default_template_no_declara_id_prefix_fijo():
    """El template/`_TAXONOMY_FALLBACK` NUNCA fijan `id_prefix` (era `"ca"` a pesar de que
    design.md:57 y el esquema documentan slug-del-proyecto como default) — lo calcula
    `cargar_taxonomia()` a partir de `root`."""
    assert "id_prefix" not in ks.default_taxonomy()
    assert "id_prefix" not in ks._TAXONOMY_FALLBACK


def test_slug_kebab_normaliza():
    assert ks._slug_kebab("Mi Proyecto_X!!") == "mi-proyecto-x"
    assert ks._slug_kebab("") == ""
    assert ks._slug_kebab("---") == ""


# ------------------------------------------------------------------ cargar_taxonomia root=None usa cwd (gap 12)

def test_cargar_taxonomia_root_none_usa_el_cwd(tmp_path, monkeypatch):
    proyecto = tmp_path / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    cfg = _valida(id_prefix="mr")
    (proyecto / "taxonomy.json").write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    config, origen, ruta, errores = ks.cargar_taxonomia()
    assert origen == "proyecto"
    assert ruta is not None
    assert errores == []
    assert config["id_prefix"] == "mr"


# ------------------------------------------------------------------ default_taxonomy nunca lanza (gap 14)

def test_default_taxonomy_con_plantilla_corrupta_cae_al_respaldo(tmp_path, monkeypatch):
    p = tmp_path / "taxonomy.json"
    p.write_bytes("{\"version\": 1}".encode("utf-16"))
    monkeypatch.setattr(ks, "TEMPLATE_PATH", str(p))
    resultado = ks.default_taxonomy()
    assert resultado == json.loads(json.dumps(ks._TAXONOMY_FALLBACK))


# ------------------------------------------------------------------ folder inseguro (gap 6, CWE-22)

def test_folder_con_traversal_falla():
    cfg = _valida(categories=[
        {"key": "X", "folder": "../candidates/pending", "min_evidence": "observation", "routing": {}},
    ])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "categories[0].folder" for e in errores)


def test_folder_absoluto_posix_falla():
    cfg = _valida(categories=[
        {"key": "X", "folder": "/etc/passwd", "min_evidence": "observation", "routing": {}},
    ])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "categories[0].folder" for e in errores)


def test_folder_con_unidad_windows_falla():
    cfg = _valida(categories=[
        {"key": "X", "folder": "C:\\evil", "min_evidence": "observation", "routing": {}},
    ])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "categories[0].folder" for e in errores)


def test_folder_colision_solo_por_mayusculas_falla():
    """Gap 38b (revision intento 3, fix4): dos `folder` que solo difieren en mayusculas/minusculas
    resuelven al MISMO directorio en un filesystem case-insensitive (NTFS por defecto en Windows);
    `validar()` debe reportarlo como error de config, no dejar que `knowledge-index.py` lo
    descubra en tiempo de escaneo."""
    cfg = _valida(categories=[
        {"key": "X", "folder": "ADR", "min_evidence": "observation", "routing": {}},
        {"key": "Y", "folder": "adr", "min_evidence": "observation", "routing": {}},
    ])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "categories[1].folder" for e in errores)


def test_folder_repetido_identico_no_es_colision():
    """Dos categorias compartiendo el MISMO `folder` (misma cadena, ej. PATTERN/GOTCHA en
    `gotchas/` de la plantilla por defecto) es legitimo, no una colision de mayusculas."""
    cfg = _valida(categories=[
        {"key": "X", "folder": "gotchas", "min_evidence": "observation", "routing": {}},
        {"key": "Y", "folder": "gotchas", "min_evidence": "observation", "routing": {}},
    ])
    errores = ks.validar(cfg, "t.json")
    assert not any(e["campo"] in ("categories[0].folder", "categories[1].folder") for e in errores)


def test_folder_simple_es_valido():
    cfg = _valida(categories=[
        {"key": "X", "folder": "adr/2026", "min_evidence": "observation", "routing": {}},
    ])
    assert ks.validar(cfg, "t.json") == []


# ------------------------------------------------------------------ evidence_levels invalido (gap 7, 13)

def test_evidence_levels_vacio_falla():
    cfg = _valida(evidence_levels=[])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "evidence_levels" for e in errores)


def test_evidence_levels_no_iterable_no_lanza_typeerror():
    cfg = _valida(evidence_levels=5)
    errores = ks.validar(cfg, "t.json")  # no debe lanzar TypeError
    assert any(e["campo"] == "evidence_levels" for e in errores)


# ------------------------------------------------------------------ routing: valor real, no solo booleano (gap 2, 10)

def test_categorias_por_backend_con_valor_distingue_summary_de_true():
    cfg = _valida(
        backends={"kwipu": {"type": "markdown-export"}},
        categories=[
            {"key": "A", "folder": "a", "min_evidence": "observation", "routing": {"kwipu": True}},
            {"key": "B", "folder": "b", "min_evidence": "observation", "routing": {"kwipu": "summary"}},
            {"key": "C", "folder": "c", "min_evidence": "observation", "routing": {"kwipu": False}},
        ],
    )
    pares = ks.categorias_por_backend_con_valor(cfg, "kwipu")
    valores = {cat["key"]: valor for cat, valor in pares}
    assert valores == {"A": True, "B": "summary"}
    assert "C" not in valores


def test_dos_taxonomias_con_routing_distinto_seleccionan_categorias_distintas():
    base = {"key": "A", "folder": "a", "min_evidence": "observation"}
    cfg_habilitada = _valida(backends={"kwipu": {"type": "markdown-export"}},
                              categories=[dict(base, routing={"kwipu": True})])
    cfg_deshabilitada = _valida(backends={"kwipu": {"type": "markdown-export"}},
                                 categories=[dict(base, routing={"kwipu": False})])
    assert [c["key"] for c in ks.categorias_por_backend(cfg_habilitada, "kwipu")] == ["A"]
    assert [c["key"] for c in ks.categorias_por_backend(cfg_deshabilitada, "kwipu")] == []


# ------------------------------------------------------------------ gap 27: taxonomy.json de usuario, UTF-16/BOM

def test_cargar_taxonomia_con_bom_utf8_no_se_rechaza(tmp_path):
    """Gap 27: `taxonomy.json` guardado como "UTF-8 with BOM" (VS Code, Notepad) es JSON valido;
    antes se leia con `encoding="utf-8"` y el BOM colaba como parte de la primera clave, asi que
    `json.load` lo rechazaba como "JSON ilegible" pese a ser valido."""
    proyecto = tmp_path / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    cfg = _valida(id_prefix="mr")
    (proyecto / "taxonomy.json").write_bytes(json.dumps(cfg).encode("utf-8-sig"))
    config, origen, _ruta, errores = ks.cargar_taxonomia(root=str(tmp_path))
    assert origen == "proyecto"
    assert errores == []
    assert config["id_prefix"] == "mr"


def test_cargar_taxonomia_en_utf16_no_lanza_unicodedecodeerror(tmp_path):
    """Gap 27: los gaps 14/15 taparon `UnicodeDecodeError` en `default_taxonomy`/`main`, pero no
    en el lector del fichero de PROYECTO dentro de `cargar_taxonomia` — un `taxonomy.json` en
    UTF-16 debe degradar a un error `{fichero, campo, mensaje}`, no a un traceback."""
    proyecto = tmp_path / ".claude" / "knowledge-services"
    proyecto.mkdir(parents=True)
    cfg = _valida(id_prefix="mr")
    (proyecto / "taxonomy.json").write_bytes(json.dumps(cfg).encode("utf-16"))
    config, origen, ruta, errores = ks.cargar_taxonomia(root=str(tmp_path))  # no debe lanzar
    assert config is None
    assert origen == "proyecto"
    assert ruta is not None
    assert len(errores) == 1
    assert "UnicodeDecodeError" in errores[0]["mensaje"]


# ------------------------------------------------------------------ gap 29: id_prefix con root=None usa el cwd

def test_id_prefix_con_root_none_usa_el_slug_del_cwd(tmp_path, monkeypatch):
    """Gap 29: `_con_id_prefix_por_defecto(config, root=None)` debia usar el cwd, igual que
    `cargar_taxonomia(root=None)` ya hace desde el gap 12 — antes caia directo a `"ca"` sin
    mirarlo."""
    proyecto = tmp_path / "Proyecto Con Nombre"
    proyecto.mkdir()
    monkeypatch.chdir(proyecto)
    config, origen, _ruta, errores = ks.cargar_taxonomia(root=None)
    assert origen == "default"
    assert errores == []
    assert config["id_prefix"] == "proyecto-con-nombre"


def test_min_evidence_no_string_produce_un_solo_error():
    """T-10 (heredado de la revisión Fase 2 intento 2, `knowledge-schema.py:274-279`): antes,
    `min_evidence: 1` (int) disparaba DOS errores (`no declara min_evidence` por el `isinstance`
    seguido de `no está en evidence_levels`, porque `1 not in evidence_levels` también es cierto
    para un entero). Un valor presente pero de tipo incorrecto es UN solo defecto, no dos."""
    cfg = _valida(categories=[
        {"key": "X", "folder": "x", "min_evidence": 1, "routing": {}},
    ])
    errores = ks.validar(cfg, "t")
    errores_min_evidence = [e for e in errores if e["campo"] == "categories[0].min_evidence"]
    assert len(errores_min_evidence) == 1
    assert "min_evidence" in errores_min_evidence[0]["mensaje"]
