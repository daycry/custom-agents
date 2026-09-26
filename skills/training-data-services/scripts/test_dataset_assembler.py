"""Tests de `dataset-assembler.py` (training-data-services T-08 y T-09).

T-08: particion anti-leakage por familia COMPLETA (CA-11) con benchmark declarado explicitamente
(sin el, el ensamblador se niega) y near-duplicates que cruzan train/benchmark excluidos del lado de
train (CA-06). T-09: solo casos Gold leidos de `validation.json` en disco (CA-03), `train.jsonl` /
`benchmark.jsonl` en formato chat con procedencia (CA-12), manifiesto con hashes por caso y un
export que nunca sobrescribe ni destruye nada (CA-08: no entrena, no sirve, no corre benchmarks).
"""
import copy
import importlib.util
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(fichero, nombre):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(HERE, fichero))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


asm = _load("dataset-assembler.py", "tds_dataset_assembler")
rec = asm.rec

CASO = {
    "family": "ramp", "variant": "steep",
    "request": "Genera una rampa de 30 grados",
    "context": {"text": "escena vacia"},
    "constraints": {"max_angle_deg": 30},
    "trajectory": [
        {"role": "system", "content": "Generas geometria.", "ts": "2026-09-25T10:00:00Z"},
        {"role": "user", "content": "Genera una rampa", "ts": "2026-09-25T10:00:01Z"},
        {"role": "assistant", "content": "", "tool_calls": [{"name": "make_ramp", "arguments": {"angle_deg": 30}}]},
        {"role": "tool", "name": "make_ramp", "content": "ok"},
        {"role": "assistant", "content": "Hecho."},
    ],
    "metrics": {"score": 0.5},
    "outcome": "success",
    "artifacts": [{"path": "final/ramp.blend", "hash": "sha256:ab12", "kind": "mesh"}],
}


def _caso(**cambios):
    c = copy.deepcopy(CASO)
    c.update(cambios)
    return c


def _proyecto(tmp_path, **extra):
    raiz = tmp_path / "proj"
    raiz.mkdir(exist_ok=True)
    cfg = {"version": 1, "enabled": True, "root": "../store", "id_prefix": "geo"}
    cfg.update(extra)
    d = raiz / ".claude" / "knowledge-services"
    d.mkdir(parents=True, exist_ok=True)
    (d / "training.json").write_text(json.dumps(cfg), encoding="utf-8")
    return str(raiz), cfg, tmp_path / "store"


def _grabar(cfg, raiz, gold=True, **cambios):
    r = rec.grabar(_caso(**cambios), cfg, raiz)
    if gold:
        rec.cambiar_estado(r["case_id"], r["version"], "approved", cfg, raiz, approved_by_human=True)
    return r


def _cli(*args, cwd=None):
    return subprocess.run([sys.executable, os.path.join(HERE, "dataset-assembler.py"), *args], cwd=cwd,
                          capture_output=True, text=True, encoding="utf-8")


def _c(ref, family):
    case_id, v = ref.split("@v")
    return {"ref": ref, "case_id": case_id, "version": int(v), "family": family}


# ------------------------------------------------------------------ T-08: particion anti-leakage

def test_t08_leakage_toda_version_de_una_familia_va_al_mismo_lado():
    casos = [_c("geo-a.x@v001", "a"), _c("geo-a.x@v002", "a"), _c("geo-a.y@v001", "a"),
             _c("geo-b.x@v001", "b"), _c("geo-b.x@v002", "b"), _c("geo-c.x@v001", "c")]
    r = asm.particionar(casos, {"b"})
    por_familia = {}
    for c in r:
        por_familia.setdefault(c["family"], set()).add(c["particion"])
    assert por_familia == {"a": {"train"}, "b": {"benchmark"}, "c": {"train"}}
    assert all(c["motivo"] is None for c in r)
    assert [c["ref"] for c in r] == sorted(c["ref"] for c in casos)


def test_t08_leakage_near_duplicate_que_cruza_la_particion_sale_de_train():
    casos = [_c("geo-a.x@v001", "a"), _c("geo-b.x@v001", "b"), _c("geo-c.x@v001", "c")]
    r = {c["ref"]: c for c in asm.particionar(casos, {"b"}, grupos=[["geo-a.x@v001", "geo-b.x@v001"]])}
    assert r["geo-a.x@v001"]["particion"] is None
    assert "cruce de particion" in r["geo-a.x@v001"]["motivo"] and "geo-b.x@v001" in r["geo-a.x@v001"]["motivo"]
    assert r["geo-b.x@v001"]["particion"] == "benchmark" and r["geo-b.x@v001"]["motivo"] is None
    assert r["geo-c.x@v001"]["particion"] == "train"


def test_t08_leakage_nunca_se_excluye_el_lado_de_benchmark_aunque_se_conserven_duplicados():
    casos = [_c("geo-a.x@v001", "a"), _c("geo-a.x@v002", "a"), _c("geo-b.x@v001", "b")]
    grupos = [["geo-a.x@v001", "geo-a.x@v002", "geo-b.x@v001"]]
    for conservar in (False, True):
        r = {c["ref"]: c for c in asm.particionar(casos, {"b"}, grupos=grupos, conservar_duplicados=conservar)}
        assert r["geo-b.x@v001"]["particion"] == "benchmark"
        assert r["geo-a.x@v001"]["particion"] is None and r["geo-a.x@v002"]["particion"] is None


def test_t08_leakage_duplicados_dentro_de_una_particion_conservan_la_version_mas_alta():
    casos = [_c("geo-a.x@v001", "a"), _c("geo-a.x@v002", "a"), _c("geo-a.x@v003", "a"), _c("geo-b.x@v001", "b")]
    grupos = [["geo-a.x@v001", "geo-a.x@v002", "geo-a.x@v003"]]
    r = {c["ref"]: c for c in asm.particionar(casos, {"b"}, grupos=grupos)}
    assert r["geo-a.x@v003"]["particion"] == "train" and r["geo-a.x@v003"]["motivo"] is None
    for ref in ("geo-a.x@v001", "geo-a.x@v002"):
        assert r[ref]["particion"] is None and "duplicado de geo-a.x@v003" in r[ref]["motivo"]
    r = {c["ref"]: c for c in asm.particionar(casos, {"b"}, grupos=grupos, conservar_duplicados=True)}
    assert {r[x]["particion"] for x in ("geo-a.x@v001", "geo-a.x@v002", "geo-a.x@v003")} == {"train"}


def test_t08_leakage_version_10_gana_a_la_9_por_numero_no_por_texto():
    """Con anchos distintos (`version_width` cambiado a mitad), "v0010" < "v009" como texto."""
    casos = [_c("geo-a.x@v009", "a"), _c("geo-a.x@v0010", "a"), _c("geo-b.x@v001", "b")]
    r = {c["ref"]: c for c in asm.particionar(casos, {"b"}, grupos=[["geo-a.x@v009", "geo-a.x@v0010"]])}
    assert r["geo-a.x@v0010"]["particion"] == "train" and r["geo-a.x@v009"]["particion"] is None


def test_t08_sin_familia_de_benchmark_se_niega_y_explica_por_que():
    casos = [_c("geo-a.x@v001", "a")]
    for vacio in (set(), [], None):
        with pytest.raises(asm.Rechazo) as e:
            asm.particionar(casos, vacio)
        assert "--benchmark" in str(e.value) and "familia" in str(e.value)


def test_t08_familia_de_benchmark_sin_casos_gold_se_niega():
    casos = [_c("geo-a.x@v001", "a"), _c("geo-b.x@v001", "b")]
    with pytest.raises(asm.Rechazo) as e:
        asm.particionar(casos, {"b", "zzz"})
    assert "zzz" in str(e.value)


def test_t08_cli_sin_benchmark_exit_1_con_motivo_y_sin_escribir_nada(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    _grabar(cfg, raiz)
    antes = sorted(os.listdir(store))
    p = _cli("--project-root", raiz)
    assert p.returncode == 1, p.stderr
    assert "--benchmark" in p.stderr and "anti-leakage" in p.stderr and "Traceback" not in p.stderr
    assert sorted(os.listdir(store)) == antes and not (store / "exports").exists()


def test_t08_cli_benchmark_por_comas_y_repetible():
    assert asm._familias_benchmark(["a,b", " c ", "a"]) == {"a", "b", "c"}
    assert asm._familias_benchmark(None) == set()
    assert asm._familias_benchmark([",", ""]) == set()
