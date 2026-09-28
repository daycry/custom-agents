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
    ruta = os.path.join(raiz, "docs", "knowledge", "candidates", "pending", "caso-geo-ramp.steep-v001.md")
    assert "area:geometria" in open(ruta, encoding="utf-8").read()
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
