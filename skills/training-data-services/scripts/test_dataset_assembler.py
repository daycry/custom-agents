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


# ------------------------------------------------------------------ T-09: ensamblador (solo Gold, export)

import hashlib
import shutil

FECHA = "20260926"


def _store_basico(tmp_path, **extra):
    """a.x (train): Gold v001 fallo + Gold v002 correccion; a.otro pending; b.x rejected; b.y
    needs_changes; bench.x Gold (benchmark)."""
    raiz, cfg, store = _proyecto(tmp_path, **extra)
    _grabar(cfg, raiz, family="a", variant="x", outcome="failure", request="rampa de treinta grados con bola roja")
    _grabar(cfg, raiz, family="a", variant="x", outcome="corrected", supersedes_case="geo-a.x@v001",
            request="torre de cinco pisos con balcon en el tercero y escalera de caracol")
    _grabar(cfg, raiz, gold=False, family="a", variant="otro", request="puente colgante de cuarenta metros")
    r = _grabar(cfg, raiz, gold=False, family="b", variant="x", request="muro de ladrillo con ventana")
    rec.cambiar_estado(r["case_id"], 1, "rejected", cfg, raiz)
    r = _grabar(cfg, raiz, gold=False, family="b", variant="y", request="arco de medio punto sobre columnas")
    rec.cambiar_estado(r["case_id"], 1, "needs_changes", cfg, raiz)
    _grabar(cfg, raiz, family="bench", variant="x", request="engranaje de doce dientes con eje de acero")
    return raiz, cfg, store


def _ensamblar(cfg, raiz, benchmark=("bench",), **kw):
    kw.setdefault("fecha", FECHA)
    return asm.ensamblar(cfg, raiz, set(benchmark), **kw)


def _lineas(ruta):
    return [json.loads(l) for l in open(ruta, encoding="utf-8").read().splitlines()]


def _manifest(r):
    return json.load(open(os.path.join(r["ruta"], "manifest.json"), encoding="utf-8"))


def test_t09_solo_gold_entra_en_el_dataset(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz)
    train = _lineas(os.path.join(r["ruta"], "train.jsonl"))
    bench = _lineas(os.path.join(r["ruta"], "benchmark.jsonl"))
    assert [l["ref"] for l in train] == ["geo-a.x@v001", "geo-a.x@v002"]
    assert [l["ref"] for l in bench] == ["geo-bench.x@v001"]
    casos = {c["ref"]: c for c in _manifest(r)["casos"]}
    for ref, status in (("geo-a.otro@v001", "pending"), ("geo-b.x@v001", "rejected"), ("geo-b.y@v001", "needs_changes")):
        assert casos[ref]["particion"] is None and casos[ref]["motivo"] == f"no Gold (validation.status = {status})"
        assert casos[ref]["sha256"] is None


def test_t09_gold_se_lee_de_validation_json_en_disco_nunca_del_indice(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    indice = store / rec.INDICE
    lineas = [json.loads(l) for l in indice.read_text(encoding="utf-8").splitlines()]
    falsas = [dict(l, status="approved") if l["case_id"] == "geo-a.otro" else
              dict(l, status="pending") if l["case_id"] == "geo-bench.x" else l for l in lineas]
    indice.write_text("".join(json.dumps(l) + "\n" for l in falsas), encoding="utf-8")
    r = _ensamblar(cfg, raiz)
    refs = [l["ref"] for l in _lineas(os.path.join(r["ruta"], "train.jsonl"))]
    assert "geo-a.otro@v001" not in refs
    assert [l["ref"] for l in _lineas(os.path.join(r["ruta"], "benchmark.jsonl"))] == ["geo-bench.x@v001"]


@pytest.mark.parametrize("humano", [False, "true", 1, None])
def test_t09_gold_exige_approved_by_human_true_en_el_fichero(tmp_path, humano):
    raiz, cfg, store = _store_basico(tmp_path)
    val = store / "cases" / "a.x" / "v002" / "validation.json"
    v = json.loads(val.read_text(encoding="utf-8"))
    v["approved_by_human"] = humano
    val.write_text(json.dumps(v), encoding="utf-8")
    r = _ensamblar(cfg, raiz, escribir=False)
    assert all(c["particion"] is None for c in r["manifest"]["casos"] if c["ref"] == "geo-a.x@v002")
    assert "geo-a.x@v002" not in json.dumps(r["lineas"]), humano


def test_t09_gold_decidido_con_los_bytes_leidos_no_con_el_recorrido(tmp_path, monkeypatch):
    """TOCTOU: si `validation.json` deja de ser Gold entre el recorrido y la lectura, manda lo leido."""
    raiz, cfg, store = _store_basico(tmp_path)
    real = rec._estado_de_cases

    def recorrido_y_cambio(*a, **k):
        salida = real(*a, **k)
        rec.cambiar_estado("geo-a.x", 2, "needs_changes", cfg, raiz)
        return salida
    monkeypatch.setattr(rec, "_estado_de_cases", recorrido_y_cambio)
    r = _ensamblar(cfg, raiz, escribir=False)
    casos = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert casos["geo-a.x@v002"]["particion"] is None
    assert "no Gold" in casos["geo-a.x@v002"]["motivo"] and "needs_changes" in casos["geo-a.x@v002"]["motivo"]


def test_t09_formato_chat_con_tool_calls_y_procedencia(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz)
    l1, l2 = _lineas(os.path.join(r["ruta"], "train.jsonl"))
    assert set(l1) == {"messages", "ref", "case_id", "version", "family", "variant", "outcome"}
    assert set(l2) == set(l1) | {"supersedes_case"}
    assert l2["supersedes_case"] == "geo-a.x@v001" and l2["outcome"] == "corrected" and l1["outcome"] == "failure"
    assert (l2["case_id"], l2["version"], l2["family"], l2["variant"]) == ("geo-a.x", 2, "a", "x")
    msgs = l1["messages"]
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "tool", "assistant"]
    assert msgs[2]["tool_calls"] == [{"name": "make_ramp", "arguments": {"angle_deg": 30}}]
    assert msgs[3] == {"role": "tool", "name": "make_ramp", "content": "ok"}
    assert all("ts" not in m for m in msgs)
    texto = open(os.path.join(r["ruta"], "train.jsonl"), encoding="utf-8").read()
    assert "final/ramp.blend" not in texto and "score" not in texto   # ni artefactos ni metricas


def test_t09_manifest_con_hash_por_caso_particion_y_parametros(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz, umbral=0.9, ventana=4, fraccion_boilerplate=0.6)
    m = _manifest(r)
    assert m["parametros"] == {"benchmark": ["bench"], "umbral": 0.9, "ventana": 4, "fraccion_boilerplate": 0.6,
                               "min_familias_boilerplate": 3, "conservar_duplicados": False}
    caso = {c["ref"]: c for c in m["casos"]}["geo-a.x@v002"]
    dir_v = store / "cases" / "a.x" / "v002"
    esperado = {f: hashlib.sha256((dir_v / f).read_bytes()).hexdigest() for f in asm.FICHEROS}
    assert caso["ficheros"] == esperado
    total = hashlib.sha256("".join(f"{f}\0{esperado[f]}\n" for f in asm.FICHEROS).encode()).hexdigest()
    assert caso["sha256"] == total and caso["particion"] == "train" and caso["motivo"] is None
    for f in ("train.jsonl", "benchmark.jsonl"):
        datos = open(os.path.join(r["ruta"], f), "rb").read()
        assert m["ficheros"][f] == {"sha256": hashlib.sha256(datos).hexdigest(), "lineas": datos.count(b"\n")}
    assert m["export_id"] == os.path.basename(r["ruta"]) and m["export_id"].startswith(FECHA + "-")
    assert m["export_id"].endswith(m["sha256_contenido"][:12])


def test_t09_near_duplicates_en_el_manifiesto_y_cruce_excluido(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    texto = "genera una rampa de treinta grados con anchura minima de medio metro y una bola de radio diez"
    _grabar(cfg, raiz, family="a", variant="x", request=texto)
    _grabar(cfg, raiz, family="a", variant="x", request=texto + " roja")
    _grabar(cfg, raiz, family="bench", variant="x", request=texto + " azul")
    _grabar(cfg, raiz, family="c", variant="x", request="algo completamente distinto sin relacion alguna con nada",
            trajectory=[{"role": "user", "content": "otra cosa"}, {"role": "assistant", "content": "vale"}])
    r = _ensamblar(cfg, raiz, umbral=0.5)
    m = _manifest(r)
    assert ["geo-a.x@v001", "geo-a.x@v002", "geo-bench.x@v001"] in m["grupos_near_duplicates"]
    casos = {c["ref"]: c for c in m["casos"]}
    for ref in ("geo-a.x@v001", "geo-a.x@v002"):
        assert casos[ref]["particion"] is None and "cruce de particion" in casos[ref]["motivo"]
    assert casos["geo-bench.x@v001"]["particion"] == "benchmark"
    assert [l["ref"] for l in _lineas(os.path.join(r["ruta"], "train.jsonl"))] == ["geo-c.x@v001"]


def test_t09_byte_determinista_para_la_misma_entrada(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    copia = tmp_path / "copia"
    shutil.copytree(str(tmp_path / "proj"), str(copia / "proj"))
    shutil.copytree(str(store), str(copia / "store"))
    r1 = _ensamblar(cfg, raiz)
    r2 = _ensamblar(cfg, str(copia / "proj"))
    assert os.path.basename(r1["ruta"]) == os.path.basename(r2["ruta"])
    for f in ("train.jsonl", "benchmark.jsonl", "manifest.json"):
        assert open(os.path.join(r1["ruta"], f), "rb").read() == open(os.path.join(r2["ruta"], f), "rb").read()


def test_t09_reensamblar_lo_mismo_no_escribe_nada(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r1 = _ensamblar(cfg, raiz)
    antes = {p: open(os.path.join(r1["ruta"], p), "rb").read() for p in os.listdir(r1["ruta"])}
    r2 = _ensamblar(cfg, raiz)
    assert r2["existente"] is True and r2["ruta"] == r1["ruta"]
    assert os.listdir(store / "exports") == [os.path.basename(r1["ruta"])]
    assert {p: open(os.path.join(r1["ruta"], p), "rb").read() for p in os.listdir(r1["ruta"])} == antes


def test_t09_nunca_sobrescribe_un_export_incompleto_con_el_mismo_id(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    export_id = _ensamblar(cfg, raiz, escribir=False)["export_id"]
    ajeno = store / "exports" / export_id
    ajeno.mkdir(parents=True)
    (ajeno / "train.jsonl").write_bytes(b"ajeno\n")
    r = _ensamblar(cfg, raiz)
    assert os.path.basename(r["ruta"]) == export_id + ".2" and r["existente"] is False
    assert (ajeno / "train.jsonl").read_bytes() == b"ajeno\n" and sorted(os.listdir(ajeno)) == ["train.jsonl"]


def test_t09_export_manipulado_con_el_mismo_id_no_cuenta_como_existente(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r1 = _ensamblar(cfg, raiz)
    with open(os.path.join(r1["ruta"], "train.jsonl"), "ab") as f:
        f.write(b'{"messages": [], "ref": "inyectado"}\n')
    r2 = _ensamblar(cfg, raiz)
    assert r2["existente"] is False and r2["ruta"] == r1["ruta"] + ".2"
    assert b"inyectado" in open(os.path.join(r1["ruta"], "train.jsonl"), "rb").read()
    assert b"inyectado" not in open(os.path.join(r2["ruta"], "train.jsonl"), "rb").read()


def test_t09_fallo_a_mitad_deja_el_export_incompleto_sin_borrar_nada(tmp_path, monkeypatch):
    raiz, cfg, store = _store_basico(tmp_path)

    def falla(*_a, **_k):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(asm, "_publicar_manifest", falla)
    with pytest.raises(OSError) as e:
        _ensamblar(cfg, raiz)
    assert "incompleto" in str(e.value) and "manifest.json" in str(e.value)
    (d,) = os.listdir(store / "exports")
    assert sorted(os.listdir(store / "exports" / d)) == ["benchmark.jsonl", "train.jsonl"]
    monkeypatch.undo()
    r = _ensamblar(cfg, raiz)
    assert os.path.basename(r["ruta"]) == d + ".2"
    assert sorted(os.listdir(store / "exports" / d)) == ["benchmark.jsonl", "train.jsonl"]


def test_t09_manifest_se_escribe_el_ultimo(tmp_path, monkeypatch):
    raiz, cfg, store = _store_basico(tmp_path)
    orden = []
    real_crear, real_pub = asm._crear, asm._publicar_manifest

    def crear(ctx, ruta, datos):
        orden.append(os.path.basename(ruta))
        return real_crear(ctx, ruta, datos)

    def publicar(ctx, d, datos):
        orden.append("manifest.json")
        return real_pub(ctx, d, datos)
    monkeypatch.setattr(asm, "_crear", crear)
    monkeypatch.setattr(asm, "_publicar_manifest", publicar)
    _ensamblar(cfg, raiz)
    assert orden == ["train.jsonl", "benchmark.jsonl", "manifest.json"]


def test_t09_version_incompleta_se_omite_con_aviso(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    os.remove(store / "cases" / "a.x" / "v001" / "request.json")
    r = _ensamblar(cfg, raiz, escribir=False)
    casos = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert casos["geo-a.x@v001"]["particion"] is None and "omitida" in casos["geo-a.x@v001"]["motivo"]
    assert "request.json" in casos["geo-a.x@v001"]["motivo"]


def test_t09_fichero_de_version_que_es_enlace_duro_se_omite(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    fuera = tmp_path / "fuera.json"
    fuera.write_text('{"request": "secreto de fuera del store"}', encoding="utf-8")
    req = store / "cases" / "a.x" / "v001" / "request.json"
    os.remove(req)
    try:
        os.link(str(fuera), str(req))
    except OSError as e:   # pragma: no cover - entorno
        pytest.skip(f"sin enlaces duros: {e}")
    r = _ensamblar(cfg, raiz, escribir=False)
    casos = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert casos["geo-a.x@v001"]["particion"] is None and "enlace duro" in casos["geo-a.x@v001"]["motivo"]
    assert "secreto de fuera" not in json.dumps(r["lineas"])


def _enlazar_dir(objetivo, enlace):
    os.makedirs(str(objetivo), exist_ok=True)
    try:
        if os.name == "nt":
            import _winapi
            _winapi.CreateJunction(str(objetivo), str(enlace))
        else:
            os.symlink(str(objetivo), str(enlace), target_is_directory=True)
    except (OSError, AttributeError, NotImplementedError) as e:   # pragma: no cover - entorno
        pytest.skip(f"no se puede crear un enlace de directorio: {e}")


def test_t09_version_que_es_un_enlace_de_directorio_no_se_exporta(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    v2 = store / "cases" / "a.x" / "v002"
    fuera = tmp_path / "fuera-v002"
    shutil.copytree(str(v2), str(fuera))
    shutil.rmtree(str(v2))
    _enlazar_dir(fuera, v2)
    r = _ensamblar(cfg, raiz, escribir=False)
    assert all(c["ref"] != "geo-a.x@v002" or c["particion"] is None for c in r["manifest"]["casos"])
    assert any("v002" in a and "enlace" in a for a in r["manifest"]["avisos"])


def test_t09_version_sustituida_por_enlace_tras_el_recorrido_no_se_lee(tmp_path, monkeypatch):
    """TOCTOU del directorio: `vNNN` pasa a ser un enlace entre el recorrido y la lectura."""
    raiz, cfg, store = _store_basico(tmp_path)
    v2 = store / "cases" / "a.x" / "v002"
    fuera = tmp_path / "fuera-v002"
    shutil.copytree(str(v2), str(fuera))
    (fuera / "request.json").write_text('{"request": "contenido ajeno"}', encoding="utf-8")
    real = rec._estado_de_cases

    def recorrido_y_enlace(*a, **k):
        salida = real(*a, **k)
        shutil.rmtree(str(v2))
        _enlazar_dir(fuera, v2)
        return salida
    monkeypatch.setattr(rec, "_estado_de_cases", recorrido_y_enlace)
    r = _ensamblar(cfg, raiz, escribir=False)
    casos = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert casos["geo-a.x@v002"]["particion"] is None and "omitida" in casos["geo-a.x@v002"]["motivo"]
    assert "contenido ajeno" not in json.dumps(r["lineas"])


def test_t09_version_sustituida_por_enlace_a_mitad_de_la_lectura_se_descarta(tmp_path, monkeypatch):
    """TOCTOU del directorio DURANTE la lectura: tras leer `request.json` (solo lo lee el ensamblador),
    `vNNN` pasa a ser un enlace a una copia con otra trayectoria; la comprobacion posterior lo ve y el
    caso no se usa."""
    raiz, cfg, store = _store_basico(tmp_path)
    v2 = store / "cases" / "a.x" / "v002"
    fuera = tmp_path / "fuera-v002"
    shutil.copytree(str(v2), str(fuera))
    (fuera / "trajectory.jsonl").write_text(json.dumps({"role": "user", "content": "contenido ajeno"}) + "\n",
                                            encoding="utf-8")
    real = rec._leer_de_version
    hecho = []

    def lector(dir_v, fichero, *a, **k):
        salida = real(dir_v, fichero, *a, **k)
        if fichero == "request.json" and os.path.basename(dir_v) == "v002" and "a.x" in dir_v and not hecho:
            hecho.append(1)
            shutil.rmtree(str(v2))
            _enlazar_dir(fuera, v2)
        return salida
    monkeypatch.setattr(rec, "_leer_de_version", lector)
    r = _ensamblar(cfg, raiz, escribir=False)
    assert hecho
    casos = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert casos["geo-a.x@v002"]["particion"] is None and "cambio durante la lectura" in casos["geo-a.x@v002"]["motivo"]
    assert "contenido ajeno" not in json.dumps(r["lineas"])


def test_t09_version_que_no_pasa_el_esquema_se_omite(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    tr = store / "cases" / "a.x" / "v001" / "trajectory.jsonl"
    tr.write_text(json.dumps({"role": "assistant", "content": "x", "reasoning": "privado"}) + "\n", encoding="utf-8")
    r = _ensamblar(cfg, raiz, escribir=False)
    casos = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert casos["geo-a.x@v001"]["particion"] is None and "esquema" in casos["geo-a.x@v001"]["motivo"]
    assert "privado" not in json.dumps(r["lineas"])


def test_t09_es_gold_exige_los_dos_campos_exactos():
    assert asm.es_gold({"status": "approved", "approved_by_human": True}) is True
    for v in ({"status": "approved", "approved_by_human": "true"}, {"status": "approved", "approved_by_human": 1},
              {"status": "approved"}, {"status": "pending", "approved_by_human": True}, None, [], "approved"):
        assert asm.es_gold(v) is False, v


def test_t09_fichero_plantado_en_el_export_recien_creado_no_se_sobrescribe(tmp_path, monkeypatch):
    raiz, cfg, store = _store_basico(tmp_path)
    real = os.mkdir

    def mkdir_y_planta(ruta, *a, **k):
        real(ruta, *a, **k)
        if os.path.basename(os.path.dirname(str(ruta))) == "exports":
            with open(os.path.join(str(ruta), "train.jsonl"), "wb") as f:
                f.write(b"plantado\n")
    monkeypatch.setattr(os, "mkdir", mkdir_y_planta)
    with pytest.raises(asm.Rechazo) as e:
        _ensamblar(cfg, raiz)
    monkeypatch.undo()
    assert "ya existia" in str(e.value) and "incompleto" in str(e.value)
    (d,) = os.listdir(store / "exports")
    assert (store / "exports" / d / "train.jsonl").read_bytes() == b"plantado\n"


def test_t09_exports_enlazado_se_rechaza_sin_escribir_fuera(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    fuera = tmp_path / "fuera-exports"
    _enlazar_dir(fuera, store / "exports")
    with pytest.raises(asm.Rechazo):
        _ensamblar(cfg, raiz)
    assert os.listdir(fuera) == []


def test_t09_final_enlazado_se_omite(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    final = store / "cases" / "a.x" / "v001" / "final"
    fuera = tmp_path / "fuera-final"
    shutil.copytree(str(final), str(fuera))
    shutil.rmtree(str(final))
    _enlazar_dir(fuera, final)
    r = _ensamblar(cfg, raiz, escribir=False)
    casos = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert casos["geo-a.x@v001"]["particion"] is None and "final" in casos["geo-a.x@v001"]["motivo"]


def test_t09_json_con_nan_se_omite(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    (store / "cases" / "a.x" / "v001" / "metrics.json").write_text('{"score": NaN}', encoding="utf-8")
    r = _ensamblar(cfg, raiz, escribir=False)
    casos = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert casos["geo-a.x@v001"]["particion"] is None and "metrics.json" in casos["geo-a.x@v001"]["motivo"]


def test_t09_dry_run_no_escribe_nada(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    antes = sorted(os.listdir(store))
    p = _cli("--project-root", raiz, "--benchmark", "bench", "--dry-run", "--fecha", FECHA)
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout)["export_id"].startswith(FECHA)
    assert sorted(os.listdir(store)) == antes


def test_t09_cli_exporta_y_resume(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    p = _cli("--project-root", raiz, "--benchmark", "bench", "--fecha", FECHA)
    assert p.returncode == 0, p.stderr
    assert "exports/" in p.stdout and "train 2" in p.stdout and "benchmark 1" in p.stdout
    p = _cli("--project-root", raiz, "--benchmark", "bench", "--fecha", FECHA)
    assert p.returncode == 0 and "ya existe" in p.stdout


def test_t09_cli_errores_sin_traceback(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    for args, code in ((("--fecha", "2026-09-26"), 2), (("--fecha", "20261399"), 2), (("--umbral", "0"), 2),
                       (("--ventana", "0"), 2), (("--boilerplate", "2"), 2)):
        p = _cli("--project-root", raiz, "--benchmark", "bench", *args)
        assert p.returncode == code, (args, p.stderr)
        assert "Traceback" not in p.stderr
    p = _cli("--project-root", raiz, "--benchmark", "nada", "--fecha", FECHA)
    assert p.returncode == 1 and "nada" in p.stderr and "Traceback" not in p.stderr
    assert not (store / "exports").exists()


def test_t09_capacidad_apagada_o_store_en_docs_knowledge_se_rechaza(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    with pytest.raises(asm.Rechazo):
        asm.ensamblar(dict(cfg, enabled=False), raiz, {"bench"}, fecha=FECHA)
    with pytest.raises(asm.Rechazo):
        asm.ensamblar(dict(cfg, root="docs/knowledge/casos"), raiz, {"bench"}, fecha=FECHA)
    assert not (store / "exports").exists()


def test_t09_el_ejemplo_de_assets_se_ensambla(tmp_path):
    """El store de ejemplo: v001 fallo rechazada (fuera) y v002 correccion Gold; la familia del
    ejemplo va a benchmark y train queda vacio (un solo caso)."""
    ejemplo = os.path.normpath(os.path.join(HERE, "..", "assets", "case-store-example"))
    raiz = tmp_path / "proj"
    raiz.mkdir()
    shutil.copytree(ejemplo, str(tmp_path / "store"))
    cfg = {"version": 1, "enabled": True, "root": "../store", "id_prefix": "geo"}
    r = asm.ensamblar(cfg, str(raiz), {"ramp"}, fecha=FECHA, escribir=False)
    casos = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert casos["geo-ramp.steep@v002"]["particion"] == "benchmark"
    assert casos["geo-ramp.steep@v001"]["motivo"] == "no Gold (validation.status = rejected)"
    assert r["lineas"]["benchmark.jsonl"][0]["supersedes_case"] == "geo-ramp.steep@v001"


def test_t09_no_entrena_ni_sirve_ni_usa_red_ni_borra():
    for fichero in ("dataset-assembler.py", "propose-from-case.py", "dedup.py"):
        fuente = open(os.path.join(HERE, fichero), encoding="utf-8").read()
        for prohibido in ("import subprocess", "import socket", "urllib", "http.client", "ollama", "torch",
                          "shutil", "os.rmdir", "os.unlink", "os.replace", "os.remove(", "os.rename("):
            assert prohibido not in fuente, (fichero, prohibido)
