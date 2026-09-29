"""Tests de `propose-from-case.py` (training-data-services T-09, CA-05).

Puente opt-in hacia `knowledge-curator`: un caso GOLD (leido del disco como en el ensamblador) se
PROPONE como candidato en `docs/knowledge/candidates/pending/`, con la forma que exige
`curator-gate.py`, creado sin sobrescribir nunca y sin aprobar nada.
"""
import copy
import importlib.util
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
GATE = os.path.join(REPO, "agent-kits", "knowledge-curator", "curator-gate.py")


def _load(fichero, nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(HERE, fichero))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pfc = _load("propose-from-case.py", "tds_propose_from_case")
rec = pfc.asm.rec

CASO = {
    "family": "ramp", "variant": "steep",
    "request": "Genera una rampa de 30 grados por la que la bola ruede sin salirse",
    "trajectory": [{"role": "user", "content": "Genera una rampa"}, {"role": "assistant", "content": "Hecha."}],
    "outcome": "failure",
}


def _proyecto(tmp_path, bridge=True, gold=True, **cambios):
    raiz = tmp_path / "proj"
    raiz.mkdir(exist_ok=True)
    cfg = {"version": 1, "enabled": True, "root": "../store", "id_prefix": "geo", "bridge_to_curator": bridge}
    d = raiz / ".claude" / "knowledge-services"
    d.mkdir(parents=True, exist_ok=True)
    (d / "training.json").write_text(json.dumps(cfg), encoding="utf-8")
    caso = copy.deepcopy(CASO)
    caso.update(cambios)
    r = rec.grabar(caso, dict(cfg, bridge_to_curator=False), str(raiz))
    if gold:
        rec.cambiar_estado(r["case_id"], r["version"], "approved", cfg, str(raiz), approved_by_human=True,
                           reviewer_note="La anchura minima evita que la bola se salga.")
    return str(raiz), cfg


def _cli(*args):
    return subprocess.run([sys.executable, os.path.join(HERE, "propose-from-case.py"), *args],
                          capture_output=True, text=True, encoding="utf-8")


def _gate(raiz, candidato, decision="approve", *extra):
    return subprocess.run([sys.executable, GATE, candidato, "--decision", decision, "--root", raiz, "--json", *extra],
                          capture_output=True, text=True, encoding="utf-8")


def _arbol(raiz):
    base = os.path.join(raiz, "docs", "knowledge")
    out = {}
    for d, _ds, fs in os.walk(base):
        for f in fs:
            p = os.path.join(d, f)
            out[os.path.relpath(p, base).replace(os.sep, "/")] = open(p, "rb").read()
    return out


def test_t09_puente_genera_un_candidato_pending_con_la_forma_del_gate(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    ruta = r["ruta"]
    assert os.path.dirname(ruta) == os.path.join(raiz, "docs", "knowledge", "candidates", "pending")
    texto = open(ruta, encoding="utf-8").read()
    fm = texto.split("---")[1]
    assert "category: GOTCHA" in fm and "evidencia: validated_case" in fm
    assert "source_cases: [geo-ramp.steep@v001]" in fm and "fuentes: [training-case:geo-ramp.steep@v001]" in fm
    assert "tags: [" in fm and "estado" not in fm
    p = _gate(raiz, ruta)
    assert p.returncode == 0, p.stdout + p.stderr
    v = json.loads(p.stdout)
    assert v["errores"] == [] and v["decision"] == "approve"


def test_t09_puente_nunca_aprueba_nada(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    antes = _arbol(raiz)
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "LESSON")
    despues = _arbol(raiz)
    nuevos = set(despues) - set(antes)
    assert nuevos == {"candidates/pending/" + os.path.basename(r["ruta"])}
    assert not any(k.startswith("approved/") for k in despues)
    assert b"estado: aprobado" not in despues["candidates/pending/" + os.path.basename(r["ruta"])]
    # la puerta del Curator dice que la FORMA vale para aprobar... y el candidato sigue en pending/
    assert _gate(raiz, r["ruta"]).returncode == 0
    assert os.path.exists(r["ruta"]) and _arbol(raiz) == despues


def test_t09_puente_sin_bridge_to_curator_exit_1_sin_escribir(tmp_path):
    raiz, cfg = _proyecto(tmp_path, bridge=False)
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert "bridge_to_curator" in str(e.value)
    p = _cli("geo-ramp.steep", "1", "--category", "GOTCHA", "--project-root", raiz)
    assert p.returncode == 1 and "bridge_to_curator" in p.stderr and "Traceback" not in p.stderr
    assert not os.path.exists(os.path.join(raiz, "docs"))


def test_t09_puente_solo_desde_un_caso_gold(tmp_path):
    raiz, cfg = _proyecto(tmp_path, gold=False)
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert "Gold" in str(e.value)
    assert not os.path.exists(os.path.join(raiz, "docs"))


def test_t09_puente_gold_se_lee_de_validation_json_no_del_indice(tmp_path):
    raiz, cfg = _proyecto(tmp_path, gold=False)
    store = os.path.join(raiz, "..", "store")
    with open(os.path.join(store, rec.INDICE), "a", encoding="utf-8") as f:
        f.write(json.dumps({"case_id": "geo-ramp.steep", "version": 1, "family": "ramp", "variant": "steep",
                            "status": "approved", "outcome": "failure", "updated_at": "2026-09-26T00:00:00Z"}) + "\n")
    with pytest.raises(pfc.Rechazo):
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")


def test_t09_puente_nunca_sobrescribe_ni_repropone(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    antes = open(r["ruta"], "rb").read()
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "LESSON")
    assert "ya" in str(e.value)
    assert open(r["ruta"], "rb").read() == antes
    nombre = os.path.basename(r["ruta"])
    for carpeta in ("needs_changes", "rejected"):
        destino = os.path.join(raiz, "docs", "knowledge", "candidates", carpeta)
        os.makedirs(destino, exist_ok=True)
        os.replace(r["ruta"], os.path.join(destino, nombre))
        with pytest.raises(pfc.Rechazo):
            pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
        assert not os.path.exists(r["ruta"])
        os.replace(os.path.join(destino, nombre), r["ruta"])
    aprobado = os.path.join(raiz, "docs", "knowledge", "approved", "gotchas")
    os.makedirs(aprobado)
    os.replace(r["ruta"], os.path.join(aprobado, nombre))
    with pytest.raises(pfc.Rechazo):
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert not os.path.exists(r["ruta"])


def test_t09_puente_categoria_de_la_taxonomia_del_proyecto(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "NO-EXISTE")
    assert "NO-EXISTE" in str(e.value)
    tax = {"version": 1, "categories": [{"key": "RECETA", "folder": "lessons", "min_evidence": "single_case"}]}
    d = os.path.join(raiz, ".claude", "knowledge-services")
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(tax, f)
    with pytest.raises(pfc.Rechazo):
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "RECETA")
    assert _gate(raiz, r["ruta"]).returncode == 0


def test_t09_puente_pending_enlazado_se_rechaza_sin_escribir_fuera(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    fuera = os.path.join(raiz, "docs", "knowledge", "approved", "gotchas")
    os.makedirs(fuera)
    cand = os.path.join(raiz, "docs", "knowledge", "candidates")
    os.makedirs(cand)
    try:
        if os.name == "nt":
            import _winapi
            _winapi.CreateJunction(fuera, os.path.join(cand, "pending"))
        else:
            os.symlink(fuera, os.path.join(cand, "pending"), target_is_directory=True)
    except (OSError, AttributeError) as e:   # pragma: no cover - entorno
        pytest.skip(f"sin enlaces de directorio: {e}")
    with pytest.raises(pfc.Rechazo):
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert os.listdir(fuera) == []


def _pending_enlazado(raiz):
    fuera = os.path.join(raiz, "docs", "knowledge", "approved", "gotchas")
    os.makedirs(fuera)
    cand = os.path.join(raiz, "docs", "knowledge", "candidates")
    os.makedirs(cand)
    try:
        if os.name == "nt":
            import _winapi
            _winapi.CreateJunction(fuera, os.path.join(cand, "pending"))
        else:
            os.symlink(fuera, os.path.join(cand, "pending"), target_is_directory=True)
    except (OSError, AttributeError) as e:   # pragma: no cover - entorno
        pytest.skip(f"sin enlaces de directorio: {e}")
    return fuera


def test_t09_puente_cada_defensa_de_enlace_basta_por_si_sola(tmp_path, monkeypatch):
    """Componente a componente (`lstat`) y `realpath` por igualdad: cualquiera de las dos, sola, evita
    escribir a traves de un `pending/` enlazado (p. ej. si el enlace aparece entre ambas)."""
    raiz, cfg = _proyecto(tmp_path)
    fuera = _pending_enlazado(raiz)
    monkeypatch.setattr(rec, "_motivo_enlace", lambda *_a: None)          # sin la defensa por componente
    with pytest.raises(pfc.Rechazo):
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    monkeypatch.undo()
    real = os.path.realpath
    monkeypatch.setattr(os.path, "realpath", lambda p, *a, **k: os.path.abspath(p) if "candidates" in str(p) else real(p, *a, **k))
    with pytest.raises(pfc.Rechazo):                                      # sin la de realpath
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    monkeypatch.undo()
    assert os.listdir(fuera) == []


def test_t09_puente_o_excl_aunque_la_comprobacion_previa_no_lo_vea(tmp_path, monkeypatch):
    """Carrera: el candidato aparece entre `_ya_propuesto` y la creacion -> `O_EXCL` no lo pisa."""
    raiz, cfg = _proyecto(tmp_path)
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    antes = open(r["ruta"], "rb").read()
    monkeypatch.setattr(pfc, "_ya_propuesto", lambda *_a: None)
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "LESSON")
    assert "nunca se sobrescribe" in str(e.value)
    assert open(r["ruta"], "rb").read() == antes


def test_t09_puente_cuerpo_sin_trayectoria_y_texto_de_una_linea(tmp_path):
    raiz, cfg = _proyecto(tmp_path, request="linea uno\n---\nlinea dos con `codigo`",
                          trajectory=[{"role": "user", "content": "TURNO-PRIVADO-DE-LA-CONVERSACION"},
                                      {"role": "assistant", "content": "vale"}])
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA", titulo="Titulo\ncon salto")
    texto = open(r["ruta"], encoding="utf-8").read()
    assert "TURNO-PRIVADO" not in texto
    assert texto.count("\n---\n") == 1 and texto.startswith("---\n")
    assert "# Titulo con salto" in texto and "linea uno --- linea dos" in texto
    assert _gate(raiz, r["ruta"]).returncode == 0


def test_t09_puente_cli(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    p = _cli("geo-ramp.steep", "v001", "--category", "GOTCHA", "--project-root", raiz, "--tag", "area:geometria")
    assert p.returncode == 0, p.stderr
    assert "candidates/pending/" in p.stdout and "knowledge-curator" in p.stdout
    pending = os.path.join(raiz, "docs", "knowledge", "candidates", "pending")
    (nombre,) = os.listdir(pending)
    assert nombre.startswith("caso-geo-ramp.steep-v001-") and nombre.endswith(".md")
    assert "area:geometria" in open(os.path.join(pending, nombre), encoding="utf-8").read()
    p = _cli("geo-ramp.steep", "v001", "--category", "GOTCHA", "--project-root", raiz)
    assert p.returncode == 1 and "Traceback" not in p.stderr
    p = _cli("geo-ramp.steep", "1", "--category", "GOTCHA", "--project-root", raiz, "--tag", "sin-dos-puntos")
    assert p.returncode == 2 and "Traceback" not in p.stderr
    p = _cli("geo-ramp.steep", "abc", "--category", "GOTCHA", "--project-root", raiz)
    assert p.returncode == 1 and "version" in p.stderr and "Traceback" not in p.stderr


def test_t09_puente_nada_de_docs_knowledge_alimenta_el_case_store():
    """Anti-leakage (una sola direccion): ni el recorder, ni el dedup, ni el ensamblador nombran el
    arbol de conocimiento; el puente solo lo lee para no re-proponer (`approved/`, una vez) y nunca
    escribe el token `aprobado`."""
    for fichero in ("dataset-assembler.py", "case-recorder.py", "dedup.py"):
        fuente = open(os.path.join(HERE, fichero), encoding="utf-8").read()
        assert "candidates" not in fuente and "approved/" not in fuente, fichero
    fuente = open(os.path.join(HERE, "propose-from-case.py"), encoding="utf-8").read()
    assert fuente.count('"approved"') == 1 and "estado: aprobado" not in fuente


# ------------------------------------------------------------------ fix1 de la Fase 3 (#119, #121, #125, #126, #128, #132)

import hashlib


def _store(raiz):
    return os.path.join(raiz, "..", "store")


def test_t09_puente_con_la_capacidad_apagada_no_propone(tmp_path):
    """#125: `proponer` exige `enabled: true` aunque `bridge_to_curator` este activo."""
    raiz, cfg = _proyecto(tmp_path)
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(dict(cfg, enabled=False), raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert "desactivado" in str(e.value)
    assert not os.path.exists(os.path.join(raiz, "docs"))


def test_t09_puente_redacta_peticion_nota_y_titulo_al_escribir(tmp_path):
    """#119 (CWE-312): `request.json` escrito por un tercero (o con un redactor viejo) con secretos
    literales: el candidato —versionado en Git— sale redactado con `redactar_estructura`."""
    raiz, cfg = _proyecto(tmp_path, gold=False)
    s1, s2, s3 = ("ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8", "AKIA" + "ABCDEFGHIJ012345",
                  "password=Hunter2024!x")
    d = os.path.join(_store(raiz), "cases", "ramp.steep", "v001")
    with open(os.path.join(d, "request.json"), "w", encoding="utf-8") as f:
        json.dump({"request": f"usa {s1} y {s2}"}, f)
    rec.cambiar_estado("geo-ramp.steep", 1, "approved", cfg, raiz, approved_by_human=True)
    vp = os.path.join(d, "validation.json")
    v = json.load(open(vp, encoding="utf-8"))
    v["reviewer_note"] = "ojo " + s3
    with open(vp, "w", encoding="utf-8") as f:
        json.dump(v, f)
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA", titulo="titulo " + s2)
    texto = open(r["ruta"], encoding="utf-8").read()
    for s in (s1, s2, s3):
        assert s not in texto, s
    assert "redactado" in texto
    assert _gate(raiz, r["ruta"]).returncode == 0


def test_t09_puente_tag_con_un_secreto_se_rechaza(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA", tags=["clave:ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3"])
    assert "tag" in str(e.value)
    assert not os.path.exists(os.path.join(raiz, "docs"))


def test_t09_puente_pending_sustituido_tras_prepararlo_se_detecta_y_se_nombra(tmp_path, monkeypatch):
    """#121 (CWE-59/367): `pending/` sustituido por un enlace a `approved/` entre `_preparar_pending` y
    la creacion: se detecta, el aviso nombra donde quedo el fichero (es el creado) y no se borra nada."""
    raiz, cfg = _proyecto(tmp_path)
    fuera = os.path.join(raiz, "docs", "knowledge", "approved", "gotchas")
    real = pfc._preparar_pending

    def preparar_y_sustituir(r):
        salida = real(r)
        os.makedirs(fuera)
        os.rmdir(salida[0])
        try:
            if os.name == "nt":
                import _winapi
                _winapi.CreateJunction(fuera, salida[0])
            else:
                os.symlink(fuera, salida[0], target_is_directory=True)
        except (OSError, AttributeError) as e:   # pragma: no cover - entorno
            pytest.skip(f"sin enlaces de directorio: {e}")
        return salida
    monkeypatch.setattr(pfc, "_preparar_pending", preparar_y_sustituir)
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    (creado,) = os.listdir(fuera)
    assert "quedo en" in str(e.value) and creado in str(e.value) and "gotchas" in str(e.value)
    assert "no borra nada" in str(e.value)


def test_t09_puente_nombre_inyectivo_con_familias_no_ascii_o_mayusculas(tmp_path):
    """#126: `geo-rampá.a` y `geo-rampé.a` (o dos que solo difieren en mayusculas) no comparten
    nombre de candidato: slug ASCII + sufijo del hash del `case_id@version` exacto."""
    a, b = pfc._nombre_candidato("geo-rampá.a@v001"), pfc._nombre_candidato("geo-rampé.a@v001")
    assert a != b and a.isascii() and b.isascii() and a.endswith(".md")
    assert pfc._nombre_candidato("geo-A.x@v001").casefold() != pfc._nombre_candidato("geo-a.x@v001").casefold()
    h = hashlib.sha256("geo-rampá.a@v001".encode("utf-8")).hexdigest()[:10]
    assert a == f"caso-geo-ramp-.a-v001-{h}.md"


def test_t09_puente_dos_familias_no_ascii_se_proponen_las_dos(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    cfg = dict(cfg, ids={"family_pattern": "[a-zá-ú]+"})
    for fam in ("rampá", "rampé"):
        r = rec.grabar(dict(copy.deepcopy(CASO), family=fam), dict(cfg, bridge_to_curator=False), raiz)
        rec.cambiar_estado(r["case_id"], 1, "approved", cfg, raiz, approved_by_human=True)
    r1 = pfc.proponer(cfg, raiz, "geo-rampá.steep", 1, "GOTCHA")
    r2 = pfc.proponer(cfg, raiz, "geo-rampé.steep", 1, "GOTCHA")
    assert r1["ruta"] != r2["ruta"] and os.path.exists(r1["ruta"]) and os.path.exists(r2["ruta"])


def test_t09_puente_taxonomia_sin_knowledge_schema_exit_2(tmp_path, monkeypatch, capsys):
    """#128 (E23): sin `agent-kits/shared/knowledge-schema.py` (paquete parcial) -> fallo cerrado."""
    raiz, cfg = _proyecto(tmp_path)
    vacio = tmp_path / "sin-shared"
    vacio.mkdir()
    monkeypatch.setattr(pfc, "_dirs_shared", lambda: [str(vacio)])
    with pytest.raises(pfc.KnowledgeServicesNoDisponible):
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert pfc.main(["geo-ramp.steep", "1", "--category", "GOTCHA", "--project-root", raiz]) == 2
    assert "knowledge-schema.py" in capsys.readouterr().err
    assert not os.path.exists(os.path.join(raiz, "docs"))


def test_t09_puente_taxonomia_ilegible_exit_2(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    with open(os.path.join(raiz, ".claude", "knowledge-services", "taxonomy.json"), "w", encoding="utf-8") as f:
        f.write("{ no es json")
    with pytest.raises(pfc.KnowledgeServicesNoDisponible):
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    p = _cli("geo-ramp.steep", "1", "--category", "GOTCHA", "--project-root", raiz)
    assert p.returncode == 2 and "taxonomia" in p.stderr and "Traceback" not in p.stderr
    assert not os.path.exists(os.path.join(raiz, "docs"))


def test_t09_puente_gold_cuyo_contenido_cambio_no_se_propone(tmp_path):
    """#132: el Gold esta atado a su contenido (`content_hash`); cambiado despues -> rechazo."""
    raiz, cfg = _proyecto(tmp_path)
    d = os.path.join(_store(raiz), "cases", "ramp.steep", "v001")
    with open(os.path.join(d, "request.json"), "w", encoding="utf-8") as f:
        json.dump({"request": "otra peticion distinta de la aprobada"}, f)
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert "content_hash" in str(e.value)
    assert not os.path.exists(os.path.join(raiz, "docs"))


def test_t09_puente_gold_sin_hash_de_aprobacion_se_propone_con_aviso(tmp_path):
    raiz, cfg = _proyecto(tmp_path)
    vp = os.path.join(_store(raiz), "cases", "ramp.steep", "v001", "validation.json")
    v = json.load(open(vp, encoding="utf-8"))
    del v["content_hash"]
    with open(vp, "w", encoding="utf-8") as f:
        json.dump(v, f)
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert os.path.exists(r["ruta"]) and any("sin hash de aprobacion" in a for a in r["avisos"])


# ------------------------------------------------------------------ fix2 de la Fase 3 (#140)

def test_t09_140_el_puente_tiene_una_sola_ventana_de_creacion(tmp_path, monkeypatch):
    """#140: el puente crea UN solo fichero (`open(…, "xb")` del candidato), y su ventana es la de
    `test_t09_puente_pending_sustituido_tras_prepararlo_se_detecta_y_se_nombra` (#121)."""
    import builtins
    raiz, cfg = _proyecto(tmp_path)
    creados, real = [], builtins.open

    def open_(ruta, modo="r", *a, **k):
        if any(c in modo for c in "wxa+"):
            creados.append((os.path.basename(str(ruta)), modo))
        return real(ruta, modo, *a, **k)
    monkeypatch.setattr(pfc, "open", open_, raising=False)
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    monkeypatch.undo()
    assert creados == [(os.path.basename(r["ruta"]), "xb")], creados


# ------------------------------------------------------------------ T-10 fix2 #178: CLI EN PROCESO

def test_t10fix2_178_cli_del_puente_en_proceso(tmp_path, capsys, monkeypatch):
    """#178: `main([...])` del puente en proceso: candidato creado (0), rechazo con su motivo (1), tag
    invalido (2, argparse), E/S (2) y sin `knowledge-schema.py` (2)."""
    raiz, _cfg = _proyecto(tmp_path)
    assert pfc.main(["geo-ramp.steep", "1", "--category", "GOTCHA", "--project-root", raiz, "--tag", "area:rampas"]) == 0
    assert "OK candidato" in capsys.readouterr().out
    assert pfc.main(["geo-ramp.steep", "1", "--category", "GOTCHA", "--project-root", raiz]) == 1
    assert "rechazado" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        pfc.main(["geo-ramp.steep", "1", "--category", "GOTCHA", "--project-root", raiz, "--tag", "mal tag"])

    def falla(exc):
        def _f(*a, **k):
            raise exc
        return _f
    monkeypatch.setattr(pfc, "proponer", falla(OSError(5, "disco")))
    assert pfc.main(["geo-ramp.steep", "1", "--category", "GOTCHA", "--project-root", raiz]) == 2
    monkeypatch.setattr(pfc, "proponer", falla(pfc.KnowledgeServicesNoDisponible("sin taxonomia")))
    assert pfc.main(["geo-ramp.steep", "1", "--category", "GOTCHA", "--project-root", raiz]) == 2
    capsys.readouterr()
