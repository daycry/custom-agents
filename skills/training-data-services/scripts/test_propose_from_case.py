"""Tests de `propose-from-case.py` (training-data-services T-09, CA-05).

Puente opt-in hacia `knowledge-curator`: un caso GOLD (leido del disco como en el ensamblador) se
PROPONE como candidato en `docs/knowledge/candidates/pending/`, con la forma que exige
`curator-gate.py`, creado sin sobrescribir nunca y sin aprobar nada.
"""
import copy
import importlib.util
import json
import os
import re
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
    # El servicio puede dejar su cerrojo/recibos de control; el unico contenido
    # de conocimiento nuevo sigue siendo este candidato, nunca un aprobado.
    assert {k for k in nuevos if k.lower().endswith(".md")} == {
        "candidates/pending/" + os.path.basename(r["ruta"])}
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
    with pytest.raises((pfc.Rechazo, pfc.KnowledgeServicesNoDisponible)):
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


def test_t09_puente_enlace_pending_se_rechaza_aun_con_realpath_no_informativo(tmp_path, monkeypatch):
    """La inspeccion de componentes del servicio no depende solo de realpath."""
    raiz, cfg = _proyecto(tmp_path)
    fuera = _pending_enlazado(raiz)
    real = os.path.realpath
    monkeypatch.setattr(os.path, "realpath", lambda p, *a, **k: os.path.abspath(p) if "candidates" in str(p) else real(p, *a, **k))
    with pytest.raises((pfc.Rechazo, pfc.KnowledgeServicesNoDisponible)):
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    monkeypatch.undo()
    assert os.listdir(fuera) == []


def test_t09_puente_publicacion_exclusiva_no_pisa_candidato_creado_en_carrera(tmp_path, monkeypatch):
    """El destino aparece justo antes del publish exclusivo real del servicio; no se pisa."""
    raiz, cfg = _proyecto(tmp_path)
    target = os.path.join(raiz, "docs", "knowledge", "candidates", "pending",
                          pfc._nombre_candidato("geo-ramp.steep@v001"))
    real_link, reached = os.link, []

    def publish_after_foreign_creation(source, destination, *args, **kwargs):
        if os.path.normcase(os.path.abspath(destination)) == os.path.normcase(target):
            reached.append(destination)
            with open(target, "xb") as f:
                f.write(b"foreign contender bytes\n")
        return real_link(source, destination, *args, **kwargs)

    monkeypatch.setattr(os, "link", publish_after_foreign_creation)
    with pytest.raises(pfc.Rechazo) as e:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert len(reached) == 1, "la carrera no alcanzo la publicacion real"
    assert open(target, "rb").read() == b"foreign contender bytes\n"
    assert str(e.value)


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


def test_t09_puente_nada_de_docs_knowledge_alimenta_el_case_store(tmp_path):
    """Anti-leakage (una sola direccion): ni el recorder, ni el dedup, ni el ensamblador nombran el
    arbol de conocimiento. Proponer no cambia ningun byte del store: solo escribe el buzon."""
    for fichero in ("dataset-assembler.py", "case-recorder.py", "dedup.py"):
        fuente = open(os.path.join(HERE, fichero), encoding="utf-8").read()
        assert "candidates" not in fuente and "approved/" not in fuente, fichero
    raiz, cfg = _proyecto(tmp_path)
    store = os.path.join(raiz, "..", "store")

    def store_bytes():
        return {os.path.relpath(os.path.join(d, f), store): open(os.path.join(d, f), "rb").read()
                for d, _, fs in os.walk(store) for f in fs}

    before = store_bytes()
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert before == store_bytes()
    assert b"estado:" not in open(r["ruta"], "rb").read()


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


def test_t09_puente_pending_sustituido_antes_del_servicio_no_escribe_en_approved(tmp_path, monkeypatch):
    """Reemplazo en la frontera productor→servicio: el preflight compartido rechaza sin escape.

    No afirma inmunidad a todo rename hostil durante IO; el viejo oraculo de escape
    post-write no era una garantia de contencion.
    """
    raiz, cfg = _proyecto(tmp_path)
    fuera = os.path.join(raiz, "docs", "knowledge", "approved", "gotchas")
    reached, load = [], pfc._cargar

    def load_with_redirect(path, name):
        mod = load(path, name)
        if os.path.basename(path) == "knowledge-curation.py":
            propose = mod.propose

            def redirect_then_propose(*args, **kwargs):
                reached.append(True)
                _pending_enlazado(raiz)
                return propose(*args, **kwargs)

            monkeypatch.setattr(mod, "propose", redirect_then_propose)
        return mod

    monkeypatch.setattr(pfc, "_cargar", load_with_redirect)
    with pytest.raises((pfc.Rechazo, pfc.KnowledgeServicesNoDisponible)):
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert reached == [True] and os.listdir(fuera) == []


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

def test_t09_140_el_puente_invoca_una_sola_persistencia_compartida(tmp_path, monkeypatch):
    """No hay segundo writer: unica llamada real al servicio, sin open de escritura local."""
    import builtins
    raiz, cfg = _proyecto(tmp_path)
    calls, load, real = [], pfc._cargar, builtins.open

    def load_observed(path, name):
        mod = load(path, name)
        if os.path.basename(path) == "knowledge-curation.py":
            propose = mod.propose

            def observe(*args, **kwargs):
                calls.append((args, kwargs))
                return propose(*args, **kwargs)

            monkeypatch.setattr(mod, "propose", observe)
        return mod

    def open_(ruta, modo="r", *a, **k):
        if any(c in modo for c in "wxa+"):
            pytest.fail("el puente conserva un open de escritura directo")
        return real(ruta, modo, *a, **k)
    monkeypatch.setattr(pfc, "_cargar", load_observed)
    monkeypatch.setattr(pfc, "open", open_, raising=False)
    r = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    monkeypatch.undo()
    assert len(calls) == 1 and os.path.isfile(r["ruta"])


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


# ------------------------------------------------------------------ B23: el puente delega persistencia en el servicio real

def test_b23_bridge_delegates_to_real_shared_propose_without_raw_writer(tmp_path, monkeypatch):
    """El mismo puente Gold conserva payload/nombre, pero no crea candidatos por su cuenta."""
    raiz, cfg = _proyecto(tmp_path)
    observed = []
    load = pfc._cargar

    def load_observed(path, name):
        mod = load(path, name)
        if os.path.basename(path) == "knowledge-curation.py":
            propose = mod.propose

            def observe(root, filename, text, **kwargs):
                observed.append((root, filename, text, kwargs))
                return propose(root, filename, text, **kwargs)

            monkeypatch.setattr(mod, "propose", observe)
        return mod

    def no_raw_write(path, mode="r", *args, **kwargs):
        assert not any(c in mode for c in "wxa+"), "bridge conserva un writer directo fuera del servicio"
        return open(path, mode, *args, **kwargs)

    monkeypatch.setattr(pfc, "_cargar", load_observed)
    monkeypatch.setattr(pfc, "open", no_raw_write, raising=False)
    result = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert len(observed) == 1, "el puente no llamó al servicio compartido real"
    project, filename, text, kwargs = observed[0]
    assert os.path.abspath(project) == os.path.abspath(raiz)
    assert filename == pfc._nombre_candidato("geo-ramp.steep@v001")
    assert kwargs.get("producer") == "training-data-services"
    assert "source_cases: [geo-ramp.steep@v001]" in text and "evidencia: validated_case" in text
    assert "trajectory" not in text and '"role"' not in text
    assert os.path.basename(result["ruta"]) == filename and os.path.isfile(result["ruta"])


def test_b23_bridge_missing_service_never_falls_back_to_raw_write(tmp_path, monkeypatch):
    """Paquete parcial con taxonomía disponible, servicio ausente: pendiente, no writer legado."""
    import shutil
    raiz, cfg = _proyecto(tmp_path)
    shared = tmp_path / "partial-shared"
    shared.mkdir()
    canonical = os.path.join(REPO, "agent-kits", "shared")
    for name in ("knowledge-schema.py", "knowledge-taxonomy-local.py"):
        shutil.copyfile(os.path.join(canonical, name), shared / name)
    monkeypatch.setattr(pfc, "_dirs_shared", lambda: [str(shared)])
    with pytest.raises(pfc.KnowledgeServicesNoDisponible) as failure:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert "knowledge-curation" in str(failure.value)
    assert not os.path.exists(os.path.join(raiz, "docs"))


def test_b23_bridge_propagates_service_rejection_without_second_writer(tmp_path, monkeypatch):
    """Un rechazo del servicio no dispara el writer previo como fallback."""
    raiz, cfg = _proyecto(tmp_path)
    observed = []
    load = pfc._cargar

    def load_rejecting(path, name):
        mod = load(path, name)
        if os.path.basename(path) == "knowledge-curation.py":
            def reject(*args, **kwargs):
                observed.append((args, kwargs))
                return {"status": "rejected", "errores": [{"mensaje": "fixture policy rejection"}], "avisos": []}, 1
            monkeypatch.setattr(mod, "propose", reject)
        return mod

    monkeypatch.setattr(pfc, "_cargar", load_rejecting)
    with pytest.raises(pfc.Rechazo) as failure:
        pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert len(observed) == 1 and "fixture policy rejection" in str(failure.value)
    assert not os.path.exists(os.path.join(raiz, "docs"))


# ------------------------------------------------------------------ revisión B23 B3: identidad Gold larga y aliases históricos

def _review_b23_long_gold(tmp_path):
    raiz, cfg = _proyecto(tmp_path, family="r" * 64, variant="s" * 64)
    second = copy.deepcopy(CASO)
    second.update(family="r" * 64, variant="s" * 63 + "t")
    record = rec.grabar(second, dict(cfg, bridge_to_curator=False), raiz)
    rec.cambiar_estado(record["case_id"], record["version"], "approved", cfg, raiz,
                       approved_by_human=True, reviewer_note="Caso largo distinto, evidencia revisada.")
    first_id = "geo-" + "r" * 64 + "." + "s" * 64
    second_id = "geo-" + "r" * 64 + "." + "s" * 63 + "t"
    assert record["case_id"] == second_id and len(first_id) == len(second_id) == 133
    for identifier in (first_id, second_id):
        family_variant = identifier[len("geo-"):]
        path = os.path.join(_store(raiz), "cases", family_variant, "v001", "validation.json")
        validation = json.load(open(path, encoding="utf-8"))
        assert validation["status"] == "approved" and validation["approved_by_human"] is True
        assert re.fullmatch(r"[a-f0-9]{64}", validation["content_hash"])
    return raiz, cfg, (first_id, second_id)


def _review_b23_store_bytes(raiz):
    store = _store(raiz)
    return {os.path.relpath(os.path.join(directory, name), store): open(os.path.join(directory, name), "rb").read()
            for directory, _, names in os.walk(store) for name in names}


def _review_b23_legacy_name(reference):
    # Fórmula exacta del baseline: el alias sólo reserva una identidad ya publicada.
    slug = re.sub(r"[^A-Za-z0-9._-]", "-", reference.replace("@", "-"))
    return "caso-" + slug + "-" + hashlib.sha256(reference.encode("utf-8")).hexdigest()[:10] + ".md"


def test_review_b23_b3_long_gold_preserves_identity_hash_and_store(tmp_path, monkeypatch):
    raiz, cfg, identifiers = _review_b23_long_gold(tmp_path)
    calls, load = [], pfc._cargar

    def observe_loader(path, name):
        mod = load(path, name)
        if os.path.basename(path) == "knowledge-curation.py":
            propose = mod.propose

            def observe(*args, **kwargs):
                calls.append(kwargs)
                return propose(*args, **kwargs)

            monkeypatch.setattr(mod, "propose", observe)
        return mod

    monkeypatch.setattr(pfc, "_cargar", observe_loader)
    store_before = _review_b23_store_bytes(raiz)
    policy = os.path.join(raiz, ".claude", "knowledge-services", "training.json")
    policy_before = open(policy, "rb").read()
    names = []
    for identifier in identifiers:
        reference = identifier + "@v001"
        result = pfc.proponer(cfg, raiz, identifier, 1, "GOTCHA")
        assert tuple(calls[-1].get("reserved_aliases", ())) == (_review_b23_legacy_name(reference),)
        name = os.path.basename(result["ruta"])
        assert name.isascii() and len(name) <= 128
        assert name == pfc._nombre_candidato(reference) == pfc._nombre_candidato(reference)
        assert name.endswith("-" + hashlib.sha256(reference.encode("utf-8")).hexdigest()[:10] + ".md")
        payload = open(result["ruta"], "rb").read()
        assert f"source_cases: [{reference}]".encode() in payload
        assert f"fuentes: [training-case:{reference}]".encode() in payload
        assert result["sha256"] == hashlib.sha256(payload).hexdigest()
        assert not os.path.exists(os.path.join(raiz, "docs", "knowledge", "approved"))
        before = _arbol(raiz)
        with pytest.raises(pfc.Rechazo):
            pfc.proponer(cfg, raiz, identifier, 1, "LESSON")
        assert before == _arbol(raiz)
        names.append(name)
    assert names[0] != names[1] and names[0].rsplit("-", 1)[0] == names[1].rsplit("-", 1)[0]
    assert _review_b23_store_bytes(raiz) == store_before
    assert open(policy, "rb").read() == policy_before
    ordinary = "geo-ramp.steep@v001"
    assert pfc._nombre_candidato(ordinary) == _review_b23_legacy_name(ordinary)


@pytest.mark.parametrize("folder", ["candidates/pending", "candidates/needs_changes",
                                    "candidates/rejected", "approved/gotchas"])
def test_review_b23_b3_long_gold_reserves_legacy_name_in_all_states(tmp_path, folder):
    raiz, cfg, identifiers = _review_b23_long_gold(tmp_path)
    reference = identifiers[0] + "@v001"
    legacy = _review_b23_legacy_name(reference)
    assert len(legacy) == 157
    destination = os.path.join(raiz, "docs", "knowledge", *folder.split("/"), legacy)
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    original = b"historical bytes kept verbatim\n"
    with open(destination, "xb") as stream:
        stream.write(original)
    store_before = _review_b23_store_bytes(raiz)
    with pytest.raises(pfc.Rechazo) as failure:
        pfc.proponer(cfg, raiz, identifiers[0], 1, "GOTCHA")
    assert "ya" in str(failure.value)
    assert open(destination, "rb").read() == original
    knowledge = _arbol(raiz)
    assert {path for path in knowledge if path.lower().endswith(".md")} == {folder + "/" + legacy}
    assert _review_b23_store_bytes(raiz) == store_before


def test_review_b23_b3_bridge_handoff_hash_is_the_service_hash(tmp_path, monkeypatch, capsys):
    raiz, cfg = _proyecto(tmp_path)
    observed, load = [], pfc._cargar

    def observing_loader(path, name):
        mod = load(path, name)
        if os.path.basename(path) == "knowledge-curation.py":
            propose = mod.propose

            def observe(*args, **kwargs):
                response = propose(*args, **kwargs)
                observed.append(response)
                return response

            monkeypatch.setattr(mod, "propose", observe)
        return mod

    monkeypatch.setattr(pfc, "_cargar", observing_loader)
    result = pfc.proponer(cfg, raiz, "geo-ramp.steep", 1, "GOTCHA")
    assert len(observed) == 1 and observed[0][1] == 0
    assert result["sha256"] == observed[0][0]["sha256"]
    assert result["sha256"] == hashlib.sha256(open(result["ruta"], "rb").read()).hexdigest()
    # Otro Gold válido permite probar salida CLI sin recrear la misma candidata.
    second = copy.deepcopy(CASO)
    second["variant"] = "gentle"
    record = rec.grabar(second, dict(cfg, bridge_to_curator=False), raiz)
    rec.cambiar_estado(record["case_id"], record["version"], "approved", cfg, raiz, approved_by_human=True)
    assert pfc.main([record["case_id"], "1", "--category", "GOTCHA", "--project-root", raiz]) == 0
    cli_output = capsys.readouterr().out
    assert observed[-1][0]["sha256"] in cli_output
