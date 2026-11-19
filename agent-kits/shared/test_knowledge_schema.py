import importlib.util
import json
import os
import sys

import pytest

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


def test_default_template_es_valido():
    assert ks.validar(ks.default_taxonomy(), "template") == []


def test_default_fallback_es_valido():
    assert ks.validar(json.loads(json.dumps(ks._TAXONOMY_FALLBACK)), "fallback") == []


def test_default_fallback_coincide_con_el_template():
    """T-01-fix1 (lint_plugin.py, ADR-016): el respaldo embebido tiene que ser el MISMO contenido
    que `templates/taxonomy.json`, no solo cada uno valido por su lado — sin este test, el
    respaldo podia divergir del canonico en SILENCIO (aqui detecta una clave que faltaba
    en uno de los dos)."""
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


def test_routing_a_backend_no_declarado_falla():
    cfg = _valida(
        backends={"docs": {"type": "adaptador-prueba"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation",
                     "routing": {"otro": True}}],
    )
    errores = ks.validar(cfg, "t.json")
    assert any("otro" in e["mensaje"] and "no declarado" in e["mensaje"] for e in errores)
    assert any(e["campo"] == "categories[0].routing.otro" for e in errores)


def test_routing_a_backend_declarado_es_valido():
    cfg = _valida(
        backends={"docs": {"type": "adaptador-prueba"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation",
                     "routing": {"docs": True}}],
    )
    assert ks.validar(cfg, "t.json") == []


def test_routing_valor_invalido():
    cfg = _valida(
        backends={"docs": {"type": "adaptador-prueba"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation",
                     "routing": {"docs": "todo"}}],
    )
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "categories[0].routing.docs" for e in errores)


def test_categoria_sin_routing_no_es_error_pero_no_exporta():
    cfg = _valida(
        backends={"docs": {"type": "adaptador-prueba"}},
        categories=[{"key": "PATTERN", "folder": "patterns", "min_evidence": "observation"}],
    )
    assert ks.validar(cfg, "t.json") == []
    assert ks.categorias_por_backend(cfg, "docs") == []


def test_backend_sin_type_falla():
    cfg = _valida(backends={"docs": {}})
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.docs.type" for e in errores)


def test_backend_enabled_no_booleano():
    cfg = _valida(backends={"docs": {"type": "adaptador-prueba", "enabled": "si"}})
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "backends.docs.enabled" for e in errores)


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


def test_default_taxonomy_con_plantilla_corrupta_cae_al_respaldo(tmp_path, monkeypatch):
    p = tmp_path / "taxonomy.json"
    p.write_bytes("{\"version\": 1}".encode("utf-16"))
    monkeypatch.setattr(ks, "TEMPLATE_PATH", str(p))
    resultado = ks.default_taxonomy()
    assert resultado == json.loads(json.dumps(ks._TAXONOMY_FALLBACK))


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


def test_evidence_levels_vacio_falla():
    cfg = _valida(evidence_levels=[])
    errores = ks.validar(cfg, "t.json")
    assert any(e["campo"] == "evidence_levels" for e in errores)


def test_evidence_levels_no_iterable_no_lanza_typeerror():
    cfg = _valida(evidence_levels=5)
    errores = ks.validar(cfg, "t.json")  # no debe lanzar TypeError
    assert any(e["campo"] == "evidence_levels" for e in errores)


def test_categorias_por_backend_con_valor_distingue_summary_de_true():
    cfg = _valida(
        backends={"docs": {"type": "adaptador-prueba"}},
        categories=[
            {"key": "A", "folder": "a", "min_evidence": "observation", "routing": {"docs": True}},
            {"key": "B", "folder": "b", "min_evidence": "observation", "routing": {"docs": "summary"}},
            {"key": "C", "folder": "c", "min_evidence": "observation", "routing": {"docs": False}},
        ],
    )
    pares = ks.categorias_por_backend_con_valor(cfg, "docs")
    valores = {cat["key"]: valor for cat, valor in pares}
    assert valores == {"A": True, "B": "summary"}
    assert "C" not in valores


def test_dos_taxonomias_con_routing_distinto_seleccionan_categorias_distintas():
    base = {"key": "A", "folder": "a", "min_evidence": "observation"}
    cfg_habilitada = _valida(backends={"docs": {"type": "adaptador-prueba"}},
                              categories=[dict(base, routing={"docs": True})])
    cfg_deshabilitada = _valida(backends={"docs": {"type": "adaptador-prueba"}},
                                 categories=[dict(base, routing={"docs": False})])
    assert [c["key"] for c in ks.categorias_por_backend(cfg_habilitada, "docs")] == ["A"]
    assert [c["key"] for c in ks.categorias_por_backend(cfg_deshabilitada, "docs")] == []


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


# ------------------------------------------------------------------ fix4 (#71/#75): defensa en
# profundidad del guardarrail de red TAMBIEN en el validador estatico (el adaptador ya la tiene).


# ------------------------------------------------------------------ setup-statusline-polish T-10/T-11
# `id_prefix` elegible y derivación de nombre (CA-14).

def _proyecto(tmp_path, nombre="mi-proyecto", taxonomy=None, manifiesto=None):
    root = tmp_path / nombre
    d = root / ".claude" / "knowledge-services"
    d.mkdir(parents=True)
    if taxonomy is not None:
        (d / "taxonomy.json").write_text(json.dumps(taxonomy), encoding="utf-8")
    if manifiesto is not None:
        (d / manifiesto[0]).write_text(json.dumps(manifiesto[1]), encoding="utf-8")
    return str(root)


def _leer_tax(root):
    with open(os.path.join(root, ks.PROJECT_TAXONOMY_REL), encoding="utf-8") as f:
        return json.load(f)


def test_CA_14_propone_el_slug_de_la_carpeta_y_valida_la_forma(tmp_path):
    root = _proyecto(tmp_path, "Mi Proyecto_X", ks.default_taxonomy())
    r = ks.preparar_id_prefix(root)
    assert r["propuesta"] == "mi-proyecto-x" and r["id_prefix"] == "mi-proyecto-x"
    assert ks.id_prefix_valido("abc-1") and not ks.id_prefix_valido("-abc")
    assert not ks.id_prefix_valido("Abc") and not ks.id_prefix_valido("a_b")
    assert not ks.id_prefix_valido("a" * 65) and not ks.id_prefix_valido("")
    assert not ks.id_prefix_valido(None)


def test_CA_14_carpeta_sin_alfanumericos_no_propone_ca(tmp_path):
    """fix1 #3: sin slug ASCII ya no cae a `ca` (lo compartian todos esos proyectos)."""
    import re
    root = _proyecto(tmp_path, "---", ks.default_taxonomy())
    propuesta = ks.proponer_id_prefix(root)
    assert propuesta != "ca" and re.fullmatch(r"p-[0-9a-f]{8}", propuesta)


def test_CA_14_sin_taxonomy_json_lo_crea_desde_la_plantilla(tmp_path):
    root = _proyecto(tmp_path, "carpeta")
    r = ks.preparar_id_prefix(root, "nuevo", aplicar=True)
    assert r["ok"] and r["escrito"]
    assert _leer_tax(root)["id_prefix"] == "nuevo"


def test_CA_14_id_prefix_invalido_rechaza_y_no_guarda(tmp_path):
    root = _proyecto(tmp_path, "carpeta", ks.default_taxonomy())
    ruta = os.path.join(root, ks.PROJECT_TAXONOMY_REL)
    antes = open(ruta, encoding="utf-8").read()
    r = ks.preparar_id_prefix(root, "Nombre Malo!", aplicar=True)
    assert r["ok"] is False and r["escrito"] is False and "id_prefix" in r["error"]
    assert open(ruta, encoding="utf-8").read() == antes


def test_CA_14_preparar_no_escribe_sin_aplicar(tmp_path):
    root = _proyecto(tmp_path, "c", ks.default_taxonomy())
    r = ks.preparar_id_prefix(root, "otro")
    assert r["ok"] and r["escrito"] is False
    assert "id_prefix" not in _leer_tax(root)


def test_CA_14_taxonomy_ilegible_o_invalida_no_se_pisa(tmp_path):
    root = _proyecto(tmp_path, "c")
    ruta = os.path.join(root, ks.PROJECT_TAXONOMY_REL)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("{no json")
    r = ks.preparar_id_prefix(root, "otro", aplicar=True)
    assert r["ok"] is False and r["escrito"] is False
    assert open(ruta, encoding="utf-8").read() == "{no json"
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("[]")
    assert ks.preparar_id_prefix(root, "otro", aplicar=True)["ok"] is False


def test_CA_14_cli_setup_id_prefix_exit_codes(tmp_path, capsys):
    root = _proyecto(tmp_path, "c", ks.default_taxonomy())
    assert ks.main(["--setup-id-prefix", "--root", root]) == 0
    assert json.loads(capsys.readouterr().out)["propuesta"] == "c"
    assert ks.main(["--setup-id-prefix", "--root", root, "--id-prefix", "MAL"]) == 2
    capsys.readouterr()
    assert ks.main(["--setup-id-prefix", "--root", root, "--id-prefix", "ok", "--aplicar"]) == 0
    assert json.loads(capsys.readouterr().out)["escrito"] is True


def test_fix1_3_mismo_nombre_no_ascii_en_rutas_distintas_da_valores_distintos(tmp_path):
    a = _proyecto(tmp_path / "uno", "知識")
    b = _proyecto(tmp_path / "dos", "知識")
    assert ks.proponer_id_prefix(a) != ks.proponer_id_prefix(b)


@pytest.mark.parametrize("carpeta,esperada", [
    ("2048", "p-2048"), ("2024", "p-2024"), ("0x1f", "p-0x1f"), ("yes", "p-yes"), ("On", "p-on"),
    ("NULL", "p-null"), ("n", "p-n"), ("mi-proyecto", "mi-proyecto"),
])
def test_fix1_2_la_propuesta_siempre_es_texto_en_yaml(tmp_path, carpeta, esperada):
    """#2: la propuesta es la clave que un backend externo puede escribir sin comillas: nunca un
    numero ni una palabra reservada de YAML 1.1 (antepone `p-`)."""
    root = _proyecto(tmp_path, carpeta)
    assert ks.proponer_id_prefix(root) == esperada


def test_fix1_18_temporal_no_predecible_ni_sigue_lo_plantado(tmp_path):
    """#18: el temporal era `taxonomy.json.<pid>.tmp`. Un directorio plantado con ese nombre hacia
    fallar la escritura; un enlace simbolico plantado desviaba la escritura a otro fichero."""
    root = _proyecto(tmp_path, "c", ks.default_taxonomy())
    ruta = os.path.join(root, ks.PROJECT_TAXONOMY_REL)
    predecible = ruta + f".{os.getpid()}.tmp"
    os.mkdir(predecible)
    r = ks.preparar_id_prefix(root, "otro", aplicar=True)
    assert r["ok"] and r["escrito"], r
    assert _leer_tax(root)["id_prefix"] == "otro"
    os.rmdir(predecible)
    victima = tmp_path / "victima.txt"
    victima.write_text("intacto", encoding="utf-8")
    try:
        os.symlink(str(victima), predecible)
    except (OSError, NotImplementedError):
        return                                   # sin enlaces simbolicos: basta el directorio
    r = ks.preparar_id_prefix(root, "otro-mas", aplicar=True)
    assert r["ok"] and victima.read_text(encoding="utf-8") == "intacto"
    assert not os.path.islink(ruta) and _leer_tax(root)["id_prefix"] == "otro-mas"


def test_fix1_18_si_falla_el_reemplazo_no_quedan_temporales(tmp_path, monkeypatch):
    root = _proyecto(tmp_path, "c", ks.default_taxonomy())
    d = os.path.dirname(os.path.join(root, ks.PROJECT_TAXONOMY_REL))
    antes = sorted(os.listdir(d))

    def falla(*a, **k):
        raise OSError("replace roto")

    monkeypatch.setattr(ks.os, "replace", falla)
    r = ks.preparar_id_prefix(root, "otro", aplicar=True)
    assert r["ok"] is False and r["escrito"] is False
    assert sorted(os.listdir(d)) == antes


# fix2 #24: `id_prefix_valido` aplica la regla del nombre de #2 (texto para YAML 1.1).
@pytest.mark.parametrize("valor", ["2048", "0x1f", "0b101", "1abc", "yes", "No", "on", "true",
                                         "null", "y", "n", "off", "false"])
def test_fix2_24_id_prefix_valido_rechaza_lo_que_yaml_no_lee_como_texto(valor):
    assert not ks.id_prefix_valido(valor)


def test_fix2_24_id_prefix_valido_admite_texto(tmp_path):
    assert ks.id_prefix_valido("abc-1") and ks.id_prefix_valido("p-2048") and ks.id_prefix_valido("yesno")


def test_fix2_24_preparar_id_prefix_rechaza_un_id_prefix_numerico(tmp_path):
    salida = ks.preparar_id_prefix(str(tmp_path), id_prefix="2048", aplicar=True)
    assert salida["ok"] is False and salida["escrito"] is False and "YAML" in salida["error"]
    assert not (tmp_path / ".claude" / "knowledge-services" / "taxonomy.json").exists()


def test_CA_14_instalacion_nueva_guarda_el_id_prefix_y_nada_mas(tmp_path):
    root = _proyecto(tmp_path, "carpeta", ks.default_taxonomy())
    r = ks.preparar_id_prefix(root, "nombre-elegido", aplicar=True)
    assert r["ok"] and r["escrito"] and "instalacion_previa" not in r
    guardado = _leer_tax(root)
    assert guardado["id_prefix"] == "nombre-elegido"
    assert guardado["backends"] == {}


def test_fix1_3_carpetas_no_ascii_dan_id_prefix_distintos_estables_y_nunca_ca(tmp_path):
    """#3: `知識` y `проект` compartian `ca` como `id_prefix`: se mezclaban sus identificadores."""
    a = _proyecto(tmp_path, "知識", ks.default_taxonomy())
    b = _proyecto(tmp_path, "проект", ks.default_taxonomy())
    pa, pb = ks.proponer_id_prefix(a), ks.proponer_id_prefix(b)
    assert pa != pb and "ca" not in (pa, pb)
    assert pa == ks.proponer_id_prefix(a) and pb == ks.proponer_id_prefix(b)      # deterministas
    assert ks.id_prefix_valido(pa) and ks.id_prefix_valido(pb)
    ra = ks.preparar_id_prefix(a, aplicar=True)
    rb = ks.preparar_id_prefix(b, aplicar=True)
    assert ra["propuesta"] == pa and rb["propuesta"] == pb
    assert _leer_tax(a)["id_prefix"] == pa != _leer_tax(b)["id_prefix"] == pb


def test_default_template_no_declara_backends_ni_routing():
    """plugin-audit-2 T-08: el plugin no incluye backends; una categoria sin `routing` no exporta."""
    tpl = ks.default_taxonomy()
    assert tpl["backends"] == {}
    assert all("routing" not in c for c in tpl["categories"])
    assert ks.validar(tpl, "template") == []


def test_taxonomia_heredada_con_backends_retirados_valida_con_reglas_genericas():
    cfg = _valida(backends={"kwipu": {"type": "markdown-export", "enabled": True, "config": {}},
                            "graphiti": {"type": "graphiti", "enabled": True, "config": {}}})
    assert ks.validar(cfg, "heredada") == []
