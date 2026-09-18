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
