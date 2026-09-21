"""Tests de `knowledge-sync.py` (knowledge-services T-07, ADR-018).

Cubre: routing aplicado ANTES de plan() (fail-closed, CA-09/CA-11), modos --dry-run/--check/
--rebuild, staging + dead-letter via outbox.py (CA-15, apply() roto no borra nada previo), y que
un adaptador `type: "test"` cargado desde fuera del árbol real del plugin recibe EXACTAMENTE las
entradas ya enrutadas (CA-12: añadir un backend no toca el núcleo).
"""
import importlib.util
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES_BACKENDS = os.path.normpath(os.path.join(HERE, "..", "..", "..", "evals", "fixtures", "knowledge-services"))


def _load(nombre_fichero, nombre_modulo):
    ruta = os.path.join(HERE, nombre_fichero)
    spec = importlib.util.spec_from_file_location(nombre_modulo, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre_modulo] = mod
    spec.loader.exec_module(mod)
    return mod


ks_sync = _load("knowledge-sync.py", "ks_sync_bajo_test")


def _taxonomy(root, categories, backend_cfg=None, enabled=True):
    cfg = {
        "version": 1,
        "id_prefix": "ks",
        "categories": categories,
        "evidence_levels": ["observation", "single_case", "validated_case",
                             "multiple_validated_cases", "human_confirmed_rule"],
        "backends": {
            "testx": {"type": "test", "enabled": enabled, "config": backend_cfg or {}},
        },
    }
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return cfg


def _entrada(root, folder, filename, id_, category, version=1, estado="aprobado", evidencia="observation"):
    d = os.path.join(root, "docs", "knowledge", "approved", folder)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, filename), "w", encoding="utf-8") as f:
        f.write(
            f"---\nid: {id_}\nversion: {version}\nestado: {estado}\ncategory: {category}\n"
            f"evidencia: {evidencia}\nfuentes:\n  - a\ntags:\n  - clave:valor\n---\n\ncuerpo de {id_}\n"
        )


def _categorias():
    return [
        {"key": "ENRUTADA", "folder": "gotchas", "min_evidence": "observation",
         "routing": {"testx": True}},
        {"key": "SIN_ROUTING", "folder": "gotchas", "min_evidence": "observation"},
        {"key": "DESACTIVADA", "folder": "adr", "min_evidence": "observation",
         "routing": {"testx": False}},
        {"key": "RESUMEN", "folder": "lessons", "min_evidence": "observation",
         "routing": {"testx": "summary"}},
    ]


# ------------------------------------------------------------------ routing antes de plan

def test_dry_run_solo_incluye_categorias_enrutadas_a_true_o_summary(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")
    _entrada(root, "gotchas", "e2.md", "e2", "SIN_ROUTING")
    _entrada(root, "adr", "e3.md", "e3", "DESACTIVADA")
    _entrada(root, "lessons", "e4.md", "e4", "RESUMEN")

    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--dry-run", "--json",
                               "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 0
    salida = json.loads(capsys.readouterr().out)
    ids = {op["id"] for op in salida["ops"]}
    assert ids == {"e1", "e4"}
    modos = {op["id"]: op["modo"] for op in salida["ops"]}
    assert modos["e1"] == "completo"
    assert modos["e4"] == "resumen"


def test_categoria_sin_routing_declarado_nunca_llega_al_adaptador(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e2.md", "e2", "SIN_ROUTING")

    ks_sync.main(["--backend", "testx", "--root", root, "--dry-run", "--json",
                  "--backends-dir", FIXTURES_BACKENDS])
    salida = json.loads(capsys.readouterr().out)
    assert salida["ops"] == []


def test_routing_false_nunca_llega_al_adaptador(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "adr", "e3.md", "e3", "DESACTIVADA")

    ks_sync.main(["--backend", "testx", "--root", root, "--dry-run", "--json",
                  "--backends-dir", FIXTURES_BACKENDS])
    salida = json.loads(capsys.readouterr().out)
    assert salida["ops"] == []


# ------------------------------------------------------------------ modos del CLI

def test_check_llama_health_y_verify_sin_tocar_publicacion(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias(), backend_cfg={"estado_salud": "sano"})
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--check", "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["health"]["estado"] == "sano"
    assert salida["verify"]["ok"] is True
    assert not os.path.isdir(os.path.join(root, ".claude", "knowledge-services", "_sync-outbox"))


def test_check_reporta_desfase_como_no_ok(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias(), backend_cfg={"desfase": ["e1"]})
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--check", "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 1
    salida = json.loads(capsys.readouterr().out)
    assert salida["verify"]["ok"] is False


def test_rebuild_recibe_todas_las_entradas_enrutadas(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")
    _entrada(root, "lessons", "e4.md", "e4", "RESUMEN")
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--rebuild", "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["rebuild"]["reconstruidos"] == 2


def test_modos_exclusivos_es_error_de_uso(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    assert ks_sync.main(["--backend", "testx", "--root", root, "--dry-run", "--check"]) == 2


# ------------------------------------------------------------------ publicacion real + outbox

def test_apply_real_publica_y_completa_en_outbox(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["apply"]["aplicados"] == 1

    dir_outbox = os.path.join(root, ".claude", "knowledge-services", "_sync-outbox", "testx")
    done = os.path.join(dir_outbox, "done")
    assert os.path.isdir(done)
    assert any(n.endswith(".json") and not n.endswith(".manifest.json") for n in os.listdir(done))


def test_reejecucion_es_idempotente_en_el_resultado(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")
    ks_sync.main(["--backend", "testx", "--root", root, "--json", "--backends-dir", FIXTURES_BACKENDS])
    capsys.readouterr()
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["apply"]["aplicados"] == 1


def test_apply_roto_reencola_con_backoff_y_no_borra_publicacion_anterior(tmp_path, capsys):
    """gap 116 (revision de dos lentes, intento 2 fix2): un fallo de `apply()` reencola con
    backoff en vez de ir directo a dead-letter (podria ser transitorio) — solo tras agotar los
    reintentos de ESE MISMO envelope cae a dead-letter (comportamiento de
    `outbox.reencolar_o_dead_letter`, ya cubierto por su propia suite)."""
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")

    # Primera corrida: publica de verdad.
    ks_sync.main(["--backend", "testx", "--root", root, "--json", "--backends-dir", FIXTURES_BACKENDS])
    capsys.readouterr()
    dir_outbox = os.path.join(root, ".claude", "knowledge-services", "_sync-outbox", "testx")
    done_antes = set(os.listdir(os.path.join(dir_outbox, "done")))

    # Segunda corrida: se fuerza el error de apply() reescribiendo taxonomy.json con el flag.
    _taxonomy(root, _categorias(), backend_cfg={"forzar_error_apply": True})
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "apply()" in err and "publicación anterior intacta" in err
    assert "envelope: reencolado" in err  # gap 116: NO dead-letter al primer fallo

    dead = os.path.join(dir_outbox, "dead-letter")
    assert not os.path.isdir(dead) or not os.listdir(dead)
    # el envelope fallido sigue vivo en outbox/, en backoff, listo para reintentarse mas tarde
    assert any(n.endswith(".json") for n in os.listdir(os.path.join(dir_outbox, "outbox")))
    # La publicacion de la primera corrida sigue intacta en done/.
    assert set(os.listdir(os.path.join(dir_outbox, "done"))) == done_antes


def test_drenaje_de_envelope_propio_reencolado_agota_intentos_y_va_a_dead_letter(tmp_path, capsys):
    """gap 128 (Critical): un envelope PROPIO reencolado tras un fallo real de `apply()` ya no se
    queda atascado para siempre — cada corrida futura lo DRENA y reintenta aplicarlo; si el
    backend sigue roto, escala de verdad (`intentos` sube en cada drenaje) hasta `MAX_INTENTOS` y
    cae a dead-letter con causa REAL (antes: nunca llegaba, se trataba como "ajeno" sin fin)."""
    root = str(tmp_path)
    _taxonomy(root, _categorias(), backend_cfg={"forzar_error_apply": True})
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")
    dir_outbox = os.path.join(root, ".claude", "knowledge-services", "_sync-outbox", "testx")

    # Primera corrida: falla, reencola con backoff (intentos=1).
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 1
    capsys.readouterr()

    ob_mod = ks_sync._cargar_por_ruta(  # noqa: SLF001
        os.path.join(ks_sync.SHARED, "outbox.py"), "ks_outbox_test_drenaje_dl")
    # libera el backoff para poder drenarlo de inmediato en la siguiente corrida (test determinista,
    # sin esperar minutos reales)
    ob_mod.reintentar_ahora(dir_outbox)

    for _ in range(2):  # de intentos=1 a intentos=3 (MAX_INTENTOS) en dos drenajes mas
        ks_sync.main(["--backend", "testx", "--root", root, "--json",
                      "--backends-dir", FIXTURES_BACKENDS])
        capsys.readouterr()
        ob_mod.reintentar_ahora(dir_outbox)

    dead = os.listdir(os.path.join(dir_outbox, "dead-letter"))
    assert any(n.endswith(".causa.json") for n in dead)
    causa_json = next(n for n in dead if n.endswith(".causa.json"))
    with open(os.path.join(dir_outbox, "dead-letter", causa_json), encoding="utf-8") as f:
        causa = json.load(f)
    assert causa["intentos"] >= 3
    assert "RuntimeError" in causa["causa"]  # causa REAL, no generica


# ------------------------------------------------------------------ backend/adaptador invalidos

def test_backend_no_declarado_es_error_de_uso(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    assert ks_sync.main(["--backend", "no-existe", "--root", root]) == 2


def test_backend_desactivado_es_error_de_uso(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _categorias(), enabled=False)
    assert ks_sync.main(["--backend", "testx", "--root", root]) == 2


def test_adaptador_incompleto_falla_al_cargar_con_mensaje_claro(tmp_path):
    root = str(tmp_path)
    incompleto_dir = os.path.join(root, "adaptadores-incompletos")
    os.makedirs(incompleto_dir, exist_ok=True)
    with open(os.path.join(incompleto_dir, "incompleto.py"), "w", encoding="utf-8") as f:
        f.write("def health(cfg):\n    return {'estado': 'sano'}\n")
    cfg = {
        "version": 1,
        "id_prefix": "ks",
        "categories": _categorias(),
        "backends": {"testx": {"type": "incompleto", "enabled": True, "config": {}}},
    }
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)

    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--check",
                              "--backends-dir", incompleto_dir])
    assert exit_code == 2


# ------------------------------------------------------------------ fix1 (2026-09-18): gaps 84/88/90/91/104

def test_check_reporta_error_de_adaptador_como_exit_1_sin_traceback(tmp_path, capsys):
    """gap 90: `health()`/`verify()` de un adaptador que lanza no tumban el CLI con traceback."""
    root = str(tmp_path)
    _taxonomy(root, _categorias(), backend_cfg={"forzar_error_health": True})
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--check",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "falló" in err and "RuntimeError" in err


def test_plan_roto_reporta_exit_1_sin_traceback(tmp_path, capsys):
    """gap 90: `plan()` de un adaptador que lanza (camino de publicación real) sale limpio."""
    root = str(tmp_path)
    _taxonomy(root, _categorias(), backend_cfg={"forzar_error_plan": True})
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "plan" in err and "RuntimeError" in err
    # no se escribió nada en la outbox: el fallo fue antes de llegar a ella
    assert not os.path.isdir(os.path.join(root, ".claude", "knowledge-services", "_sync-outbox"))


def test_omitidas_por_routing_se_informan_por_stderr(tmp_path, capsys):
    """gap 84: una entrada sin routing para este backend no desaparece en silencio."""
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")
    _entrada(root, "gotchas", "e2.md", "e2", "SIN_ROUTING")
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--dry-run", "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 0
    err = capsys.readouterr().err
    assert "omitida" in err and "e2" in err


def test_reclamar_recoge_el_envelope_propio_aunque_haya_otro_pendiente(tmp_path, capsys):
    """gap 91/128: si `outbox/` ya tenía un envelope PROPIO pendiente de una corrida anterior (p.
    ej. un proceso muerto a medias con `apply()` reencolado), `_drenar_outbox_propia` lo DRENA
    (lo aplica y completa) ANTES de escribir el envelope fresco de esta corrida — ya no se queda
    reencolado para siempre (gap 128, corrige la deuda declarada en #116/#120: antes un envelope
    propio pendiente se trataba como "ajeno" indefinidamente)."""
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")

    ob_mod = ks_sync._cargar_por_ruta(  # noqa: SLF001 - reuso deliberado en el propio test
        os.path.join(ks_sync.SHARED, "outbox.py"), "ks_outbox_test_reclamar")
    dir_outbox = os.path.join(root, ".claude", "knowledge-services", "_sync-outbox", "testx")
    ob_mod.escribir(dir_outbox, "sync-0-pendiente-propio", {"backend": "testx", "type": "test", "ops": []})

    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["apply"]["aplicados"] == 1
    # el envelope propio pendiente se drenó (aplicado y completado), no se quedó reencolado
    assert not os.path.isfile(os.path.join(dir_outbox, "outbox", "sync-0-pendiente-propio.json"))
    assert os.path.isfile(os.path.join(dir_outbox, "done", "sync-0-pendiente-propio.json"))


def test_drenaje_cede_el_paso_a_envelope_de_otro_backend_sin_incrementar_intentos(tmp_path, capsys):
    """gap 120/128: un envelope de OTRO backend/productor no se aplica ni se pierde — se le cede
    el paso (`outbox.ceder_paso`, sin tocar su `.intentos`) y sigue disponible para quien deba
    procesarlo."""
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")

    ob_mod = ks_sync._cargar_por_ruta(  # noqa: SLF001
        os.path.join(ks_sync.SHARED, "outbox.py"), "ks_outbox_test_devolver")
    dir_outbox = os.path.join(root, ".claude", "knowledge-services", "_sync-outbox", "testx")
    ob_mod.escribir(dir_outbox, "sync-0-ajeno", {"backend": "otro-backend", "type": "test", "ops": []})

    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--json",
                              "--backends-dir", FIXTURES_BACKENDS])
    assert exit_code == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["apply"]["aplicados"] == 1
    sidecar_path = os.path.join(dir_outbox, "outbox", "sync-0-ajeno.json.intentos")
    assert os.path.isfile(os.path.join(dir_outbox, "outbox", "sync-0-ajeno.json"))
    with open(sidecar_path, encoding="utf-8") as f:
        sidecar = json.load(f)
    assert sidecar["intentos"] == 0
    assert sidecar["no_antes_de"] > 0  # cortesia, para no ser reclamado de inmediato otra vez


def test_outbox_status_imprime_estado_sin_tocar_taxonomia(tmp_path, capsys):
    """gap 120: `--outbox-status` reemplaza la referencia fantasma a un `--check` de la outbox
    (que nunca existió) por un flag real; funciona incluso sin `taxonomy.json` valido, porque solo
    necesita `outbox.estado()`."""
    root = str(tmp_path)
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--outbox-status", "--json"])
    assert exit_code == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["backend"] == "testx"
    assert "outbox" in salida
    assert salida["outbox"]["outbox"] == 0  # cola vacia (nunca se escribio nada todavia)


def test_apply_exitoso_purga_done_antiguo(tmp_path, monkeypatch):
    """gap 125 (segunda mitad): tras `completar()`, se purga `done/` por retencion — sin esto
    crecia sin limite con un `.manifest.json` por corrida para siempre. gap 139 (fix3): el
    throttle de `_purgar_done_con_throttle` (como mucho una purga real cada `_PURGA_DONE_CADA_S`)
    se desactiva aqui (`0`) para poder purgar dos veces seguidas dentro del mismo test."""
    monkeypatch.setattr(ks_sync, "_PURGA_DONE_CADA_S", 0)
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")
    ks_sync.main(["--backend", "testx", "--root", root, "--json", "--backends-dir", FIXTURES_BACKENDS])
    dir_outbox = os.path.join(root, ".claude", "knowledge-services", "_sync-outbox", "testx")
    done_dir = os.path.join(dir_outbox, "done")
    manifest_viejo = next(f for f in os.listdir(done_dir) if f.endswith(".manifest.json"))
    manifest_path = os.path.join(done_dir, manifest_viejo)
    with open(manifest_path, encoding="utf-8") as f:
        datos = json.load(f)
    datos["completado_en"] = "2020-01-01T00:00:00Z"  # muy anterior a RETENCION_DONE_DIAS
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(datos, f)

    _entrada(root, "gotchas", "e2.md", "e2", "ENRUTADA")
    ks_sync.main(["--backend", "testx", "--root", root, "--json", "--backends-dir", FIXTURES_BACKENDS])
    assert not os.path.isfile(manifest_path)  # se purgo tras la segunda publicacion


def test_entradas_enrutadas_no_reabren_el_fichero_md(tmp_path, monkeypatch):
    """gap 104: `_construir_entradas_enrutadas` usa los campos que ya trae `build_index()`
    (`category`/`evidencia`/`fuentes`/`tags`/`cuerpo`) en vez de reabrir cada `.md`."""
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")

    ki = ks_sync._cargar_por_ruta(  # noqa: SLF001
        os.path.join(ks_sync.SHARED, "knowledge-index.py"), "ks_ki_test_no_reread")
    ks = ks_sync._cargar_por_ruta(os.path.join(ks_sync.SHARED, "knowledge-schema.py"), "ks_ks_test_no_reread")
    indice, errores = ki.build_index(root)
    assert errores == []

    aperturas = []
    real_open = open

    def _open_espia(ruta, *a, **kw):
        aperturas.append(ruta)
        return real_open(ruta, *a, **kw)

    config, _o, _r, _e = ks.cargar_taxonomia(root)
    monkeypatch.setattr("builtins.open", _open_espia)
    entradas, errores_e, omitidas = ks_sync._construir_entradas_enrutadas(  # noqa: SLF001
        ki, ks, root, config, "testx", indice)
    assert errores_e == []
    assert len(entradas) == 1
    assert entradas[0]["cuerpo"].strip() == "cuerpo de e1"
    assert not any(a.endswith("e1.md") for a in aperturas)


def test_export_dir_relativo_del_backend_recibe_root_absoluto(tmp_path, capsys):
    """gap 88: el `cfg` que llega al adaptador trae `_root` absoluto (nunca depende del cwd del
    proceso que invoca `knowledge-sync.py`)."""
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "e1.md", "e1", "ENRUTADA")
    capturado = {}
    adaptador_dir = os.path.join(root, "adaptador-espia")
    os.makedirs(adaptador_dir, exist_ok=True)
    with open(os.path.join(adaptador_dir, "espia.py"), "w", encoding="utf-8") as f:
        f.write(
            "def health(cfg):\n    return {'estado': 'sano'}\n"
            "def plan(entries, cfg):\n"
            "    import json, os\n"
            "    with open(os.path.join(os.path.dirname(__file__), 'visto.json'), 'w') as fh:\n"
            "        json.dump({'root': cfg.get('_root')}, fh)\n"
            "    return []\n"
            "def apply(ops, cfg):\n    return {'aplicados': 0}\n"
            "def verify(cfg):\n    return {'ok': True, 'desfase': []}\n"
            "def rebuild(entries, cfg):\n    return {'reconstruidos': 0}\n"
            "def revoke(knowledge_id, cfg):\n    return {'revocado': knowledge_id}\n"
        )
    taxonomy = {
        "version": 1, "id_prefix": "ks", "categories": _categorias(),
        "evidence_levels": ["observation"],
        "backends": {"testx": {"type": "espia", "enabled": True, "config": {}}},
    }
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(taxonomy, f)
    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--dry-run",
                              "--backends-dir", adaptador_dir])
    assert exit_code == 0
    with open(os.path.join(adaptador_dir, "visto.json"), "r", encoding="utf-8") as f:
        visto = json.load(f)
    assert visto["root"] == os.path.abspath(root)


def test_adaptador_tipo_desconocido_falla_al_cargar_con_mensaje_claro(tmp_path, capsys):
    root = str(tmp_path)
    cfg = {
        "version": 1,
        "id_prefix": "ks",
        "categories": _categorias(),
        "backends": {"testx": {"type": "no-existe", "enabled": True, "config": {}}},
    }
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)

    exit_code = ks_sync.main(["--backend", "testx", "--root", root, "--check"])
    assert exit_code == 2
    assert "no se encontró un adaptador" in capsys.readouterr().err


# ------------------------------------------------------------------ fix4 (#72/#77)

def _adaptador_tmp(tmp_path, tipo, cuerpo_extra=""):
    """Escribe un adaptador de fixture completo (`backend_<tipo>.py`) en una carpeta propia y
    devuelve esa carpeta, para pasarla por `--backends-dir` (CA-12: el nucleo no cambia)."""
    d = tmp_path / f"adaptadores-{tipo}"
    d.mkdir(exist_ok=True)
    (d / f"backend_{tipo}.py").write_text(
        "def health(cfg):\n    return {'estado': 'sano'}\n\n"
        "def plan(entries, cfg):\n    return []\n\n"
        "def apply(ops, cfg):\n    return {'aplicados': 0}\n\n"
        "def verify(cfg):\n    return {'ok': True, 'desfase': []}\n\n"
        "def rebuild(entries, cfg):\n    return {'aplicados': 0}\n\n"
        "def revoke(kid, cfg):\n    return {'revocado': False}\n\n" + cuerpo_extra,
        encoding="utf-8")
    return str(d)


def test_fix4_gap77_el_nucleo_no_nombra_ningun_backend_concreto(tmp_path):
    """Gap #77 (Important): `improvement-plan.md:17` declara el invariante «el nucleo de
    `knowledge-sync.py` no lo nombra» (ADR-018, CA-12) y `--propose-config` lo rompio con
    `if tipo != "graphiti"` + la carga de `graphiti_model.py` por ruta DESDE el nucleo. Mutante:
    devolver cualquiera de esas dos lineas al nucleo."""
    fuente = io.open(os.path.join(HERE, "knowledge-sync.py"), encoding="utf-8").read()
    assert "graphiti" not in fuente.lower()


def test_fix4_gap77_propose_config_delega_en_la_funcion_opcional_del_adaptador(tmp_path, capsys):
    """El nucleo llama a `proponer_config(taxonomy, cfg)` SI el adaptador la define; el contenido
    de la propuesta es cosa del backend."""
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    dir_adaptador = _adaptador_tmp(
        tmp_path, "test",
        "def proponer_config(taxonomy, cfg):\n"
        "    return {'texto': 'PROPUESTA DEL ADAPTADOR', 'entity_map': {'X': 'Y'}}\n")
    rc = ks_sync.main(["--backend", "testx", "--root", root, "--propose-config",
                       "--backends-dir", dir_adaptador])
    assert rc == 0
    assert "PROPUESTA DEL ADAPTADOR" in capsys.readouterr().out


def test_fix4_gap77_propose_config_en_un_backend_que_no_la_define_lo_dice_sin_traceback(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    rc = ks_sync.main(["--backend", "testx", "--root", root, "--propose-config",
                       "--backends-dir", FIXTURES_BACKENDS])
    assert rc == 2
    assert "no propone configuraci" in capsys.readouterr().err


def test_fix4_gap72_causa_con_ansi_del_adaptador_se_sanea_antes_de_imprimirla(tmp_path, capsys):
    """Gap #72 (Important, CWE-117): `knowledge-sync.py` interpolaba `{e}` tal cual (`:183`,
    `:387`, `:450`), asi que el texto CRUDO del servidor (secuencias ANSI, CRLF, 3 000
    caracteres) llegaba a stderr y a la `causa` persistida en la dead-letter. Mutante: quitar
    `_sanear_causa` de esos tres puntos."""
    root = str(tmp_path)
    _taxonomy(root, _categorias())
    _entrada(root, "gotchas", "GOT-001.md", "ks.gotchas.uno", "ENRUTADA")
    dir_adaptador = _adaptador_tmp(
        tmp_path, "test",
        "def _explota():\n"
        "    raise RuntimeError('\\x1b[2Jbanner falso\\r\\n' + 'A' * 3000)\n")
    # `plan` del adaptador de fixture no explota: se sustituye por uno que si lo hace
    ruta = os.path.join(dir_adaptador, "backend_test.py")
    fuente = io.open(ruta, encoding="utf-8").read().replace(
        "def plan(entries, cfg):\n    return []", "def plan(entries, cfg):\n    _explota()")
    io.open(ruta, "w", encoding="utf-8").write(fuente)
    rc = ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", dir_adaptador])
    err = capsys.readouterr().err
    assert rc == 1
    assert "\x1b" not in err
    assert "banner falso" in err
    assert len(err) < 1000
