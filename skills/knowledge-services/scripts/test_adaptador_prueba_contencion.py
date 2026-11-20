"""Contencion de rutas del adaptador de PRUEBA (plugin-audit-2 T-10 fix1, gap 4: CWE-22/73).

La guia `references/add-backend.md` presenta el adaptador como ejemplo de referencia: lo que haga
con las rutas es lo que un adaptador propio copiara. Ninguna operacion puede leer, escribir ni
borrar fuera de la carpeta de publicacion (`dir`), que a su vez debe quedar dentro de `_root`,
aunque `manifest.json` (un fichero del disco, no de confianza) diga otra cosa.
"""
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def load():
    spec = importlib.util.spec_from_file_location("adaptador_prueba_contencion",
                                                  HERE / "fixtures" / "adaptador_prueba.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _proyecto_con_manifiesto_hostil(tmp_path, rutas):
    proj = tmp_path / "proj"
    out = proj / "out"
    out.mkdir(parents=True)
    victima = proj / "VICTIMA.txt"
    victima.write_text("no tocar", encoding="utf-8")
    entries = {"e%d" % i: {"hash": "0", "ruta": r} for i, r in enumerate(rutas)}
    (out / "manifest.json").write_text(json.dumps({"entries": entries}), encoding="utf-8")
    return proj, victima, {"dir": "out", "_root": str(proj)}


def test_revoke_no_borra_una_ruta_del_manifiesto_fuera_de_dir(tmp_path):
    proj, victima, cfg = _proyecto_con_manifiesto_hostil(tmp_path, ["../VICTIMA.txt"])
    load().revoke("e0", cfg)
    assert victima.read_text(encoding="utf-8") == "no tocar"


def test_rebuild_no_borra_rutas_del_manifiesto_fuera_de_dir(tmp_path):
    proj, victima, cfg = _proyecto_con_manifiesto_hostil(
        tmp_path, ["../VICTIMA.txt", str(tmp_path / "proj" / "VICTIMA.txt")])
    load().rebuild([{"id": "owned.rule", "version": 1, "cuerpo": "x"}], cfg)
    assert victima.read_text(encoding="utf-8") == "no tocar"


def test_verify_no_lee_fuera_de_dir(tmp_path):
    proj, victima, cfg = _proyecto_con_manifiesto_hostil(tmp_path, ["../VICTIMA.txt"])
    res = load().verify(cfg)
    assert res["ok"] is False and res["desfase"], res


@pytest.mark.parametrize("dir_", ["../fuera", "/abs/fuera", r"C:\fuera", "out/../../fuera"])
def test_un_dir_que_se_sale_de_root_se_rechaza(tmp_path, dir_):
    proj = tmp_path / "proj"
    proj.mkdir()
    adapter = load()
    cfg = {"dir": dir_, "_root": str(proj)}
    assert adapter.health(cfg)["estado"] == "error"
    with pytest.raises(ValueError):
        adapter.apply([], cfg)
    assert not (tmp_path / "fuera").exists()


def test_un_dir_relativo_dentro_de_root_sigue_funcionando(tmp_path):
    adapter = load()
    cfg = {"dir": "out/sub", "_root": str(tmp_path)}
    entry = {"id": "owned.rule", "version": 1, "cuerpo": "Approved."}
    adapter.apply(adapter.plan([entry], cfg), cfg)
    assert adapter.verify(cfg)["ok"] is True
    assert adapter.revoke("owned.rule", cfg)["revocado"] is True
    assert not (tmp_path / "out" / "sub" / "owned.rule.md").exists()


def test_un_id_con_separadores_no_escribe_fuera_de_dir(tmp_path):
    adapter = load()
    cfg = {"dir": "out", "_root": str(tmp_path)}
    ops = [{"accion": "upsert", "id": "../ESCAPE", "version": 1, "cuerpo": "x", "hash": "h"}]
    with pytest.raises(ValueError):
        adapter.apply(ops, cfg)
    assert not (tmp_path / "ESCAPE.md").exists()
