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


def _exports(store):
    """Los exports de `exports/` (sin el `.lock` de la exclusion entre ensambladores, #124)."""
    return sorted(n for n in os.listdir(store / "exports") if n != ".lock")


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
                               "n_min_boilerplate": 20, "presupuesto": 10 ** 7, "tope_fichero": asm.TOPE_FICHERO,
                               "conservar_duplicados": False}
    assert m["near_duplicates"] == {"jaccard": "exacto", "muestreo": {"r": 1.0, "presupuesto": 10 ** 7,
                                                                      "shingles": m["near_duplicates"]["muestreo"]["shingles"]},
                                    "cruce": {"criterio": "umbral"}}                     # #145: con r = 1, el umbral
    assert m["cruces_near_duplicates"] == []
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
    assert sorted(os.listdir(store / "exports")) == [".lock", os.path.basename(r1["ruta"])]
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
    (d,) = _exports(store)
    assert sorted(os.listdir(store / "exports" / d)) == ["benchmark.jsonl", "train.jsonl"]
    monkeypatch.undo()
    r = _ensamblar(cfg, raiz)
    assert os.path.basename(r["ruta"]) == d + ".2"
    assert sorted(os.listdir(store / "exports" / d)) == ["benchmark.jsonl", "train.jsonl"]


def test_t09_manifest_se_escribe_el_ultimo(tmp_path, monkeypatch):
    raiz, cfg, store = _store_basico(tmp_path)
    orden = []
    real_crear, real_pub = asm._abrir_export, asm._publicar_manifest

    def crear(ctx, ruta):
        orden.append(os.path.basename(ruta))
        return real_crear(ctx, ruta)

    def publicar(ctx, d, datos):
        orden.append("manifest.json")
        return real_pub(ctx, d, datos)
    monkeypatch.setattr(asm, "_abrir_export", crear)
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
    # #117: los avisos del RECORRIDO no entran en el manifiesto (dependen del reloj): van aparte
    assert any("v002" in a and "enlace" in a for a in r["avisos_store"])
    assert not any("enlace" in a for a in r["manifest"]["avisos"])


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
    (d,) = _exports(store)
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


# ------------------------------------------------------------------ fix1 de la Fase 3 (#114-#133)

import time
import tracemalloc


def _gold_ruta(store, fam_var, v):
    return store / "cases" / fam_var / f"v{v:03d}"


def test_t09_117_tmp_huerfano_envejecido_no_cambia_el_export_id(tmp_path):
    """#117: un `.tmp-*` del store «en curso» y despues «huerfano» (el aviso lleva «hace N s»): el
    `export_id` y los bytes del manifiesto solo dependen de los casos y los parametros."""
    raiz, cfg, store = _store_basico(tmp_path)
    tmp = store / ".tmp-deadbeefdeadbeef"
    tmp.write_bytes(b"x")
    r1 = _ensamblar(cfg, raiz)
    assert any("temporal" in a for a in r1["avisos_store"])
    viejo = time.time() - 3600
    os.utime(str(tmp), (viejo, viejo))
    r2 = _ensamblar(cfg, raiz)
    assert r2["export_id"] == r1["export_id"] and r2["existente"] is True and r2["ruta"] == r1["ruta"]
    assert _exports(store) == [os.path.basename(r1["ruta"])]
    assert "temporal" not in open(os.path.join(r1["ruta"], "manifest.json"), encoding="utf-8").read()


def test_t09_117_export_id_depende_solo_de_casos_y_parametros(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    a = _ensamblar(cfg, raiz, escribir=False)["export_id"]
    assert _ensamblar(cfg, raiz, escribir=False, umbral=0.7)["export_id"] != a
    (store / "cases" / "a.x" / "v001" / ".tmp-0011223344556677").write_bytes(b"y")   # otro aviso del store
    assert _ensamblar(cfg, raiz, escribir=False)["export_id"] == a


def test_t09_118_export_sustituido_por_enlace_se_detecta_y_se_nombra(tmp_path, monkeypatch):
    """#118 (CWE-59/367): `exports/<id>` sustituido por un enlace a `docs/knowledge/approved/…` entre
    la comprobacion y la creacion. El fichero aparece fuera: se detecta, el aviso NOMBRA donde quedo
    (solo si es el fichero creado, `samestat`) escapado, y no se borra nada."""
    raiz, cfg, store = _store_basico(tmp_path)
    curado = tmp_path / "proj" / "docs" / "knowledge" / "approved" / "lessons"
    curado.mkdir(parents=True)
    real = rec._Canon.comprobar_dir

    def comprobar_y_sustituir(self, ruta):
        real(self, ruta)
        if os.path.basename(os.path.dirname(ruta)) == "exports":
            os.rmdir(ruta)
            _enlazar_dir(curado, ruta)
    monkeypatch.setattr(rec._Canon, "comprobar_dir", comprobar_y_sustituir)
    with pytest.raises(asm.Rechazo) as e:
        _ensamblar(cfg, raiz)
    monkeypatch.undo()
    msg = str(e.value)
    assert "train.jsonl" in msg and "quedo en" in msg and "lessons" in msg and "incompleto" in msg
    assert "no borra nada" in msg
    assert sorted(os.listdir(curado)) == ["train.jsonl"]        # nada mas se escribio a traves del enlace


def _secretos():
    return "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8", "AKIA" + "ABCDEFGHIJ012345", "password=Hunter2024!x"


def test_t09_119_train_jsonl_se_redacta_al_escribir(tmp_path):
    """#119 (CWE-312): un secreto que llega al disco sin redactar (tercero, redactor viejo) no sale en
    `train.jsonl`: se redacta con `redactar_estructura` del recorder al escribir."""
    raiz, cfg, store = _proyecto(tmp_path)
    r = _grabar(cfg, raiz, gold=False, family="a", variant="x")
    _grabar(cfg, raiz, family="bench", variant="x", request="engranaje de doce dientes")
    d = _gold_ruta(store, "a.x", 1)
    s1, s2, s3 = _secretos()
    (d / "request.json").write_text(json.dumps({"request": "usa " + s1}), encoding="utf-8")
    (d / "trajectory.jsonl").write_text(
        json.dumps({"role": "user", "content": "clave " + s2}) + "\n"
        + json.dumps({"role": "assistant", "content": "", "tool_calls": [{"name": "t", "arguments": {"x": s3}}]})
        + "\n", encoding="utf-8")
    rec.cambiar_estado(r["case_id"], 1, "approved", cfg, raiz, approved_by_human=True)
    out = _ensamblar(cfg, raiz)
    texto = open(os.path.join(out["ruta"], "train.jsonl"), encoding="utf-8").read()
    assert "geo-a.x@v001" in texto
    for s in (s2, s3):
        assert s not in texto
    assert "redactado" in texto


def test_t09_120_cadena_fallo_correccion_no_se_descarta_por_duplicado():
    """#120 (design.md:42, CA-12): v1 failure + v2 corrected (supersedes v1) + v3 failure en un grupo:
    los de la cadena se conservan; la regla «version mas alta» solo entre lo que no es cadena."""
    casos = [dict(_c("geo-a.x@v001", "a")), dict(_c("geo-a.x@v002", "a"), supersedes_case="geo-a.x@v001"),
             dict(_c("geo-a.x@v003", "a")), dict(_c("geo-a.x@v004", "a")), _c("geo-b.x@v001", "b")]
    grupos = [["geo-a.x@v001", "geo-a.x@v002", "geo-a.x@v003", "geo-a.x@v004"]]
    r = {c["ref"]: c for c in asm.particionar(casos, {"b"}, grupos=grupos)}
    for ref in ("geo-a.x@v001", "geo-a.x@v002", "geo-a.x@v004"):
        assert r[ref]["particion"] == "train" and r[ref]["motivo"] is None, ref
    assert r["geo-a.x@v003"]["particion"] is None and "duplicado de geo-a.x@v004" in r["geo-a.x@v003"]["motivo"]


def test_t09_120_par_fallo_correccion_solo_se_conserva_entero():
    casos = [_c("geo-a.x@v001", "a"), dict(_c("geo-a.x@v002", "a"), supersedes_case="geo-a.x@v001"),
             _c("geo-b.x@v001", "b")]
    r = {c["ref"]: c for c in asm.particionar(casos, {"b"}, grupos=[["geo-a.x@v001", "geo-a.x@v002"]])}
    assert r["geo-a.x@v001"]["particion"] == "train" and r["geo-a.x@v002"]["particion"] == "train"
    # el cruce de particion sigue mandando sobre la cadena (anti-leakage)
    r = {c["ref"]: c for c in asm.particionar(casos, {"b"},
                                              grupos=[["geo-a.x@v001", "geo-a.x@v002", "geo-b.x@v001"]])}
    assert r["geo-a.x@v001"]["particion"] is None and r["geo-a.x@v002"]["particion"] is None


def test_t09_120_en_el_export_el_par_fallo_correccion_llega_entero(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    texto = "genera una rampa de treinta grados con anchura minima de medio metro y una bola de radio diez"
    _grabar(cfg, raiz, family="a", variant="x", outcome="failure", request=texto)
    _grabar(cfg, raiz, family="a", variant="x", outcome="corrected", supersedes_case="geo-a.x@v001",
            request=texto + " roja")
    _grabar(cfg, raiz, family="bench", variant="x", request="engranaje de doce dientes con eje de acero",
            trajectory=[{"role": "user", "content": "otra cosa"}, {"role": "assistant", "content": "vale"}])
    r = _ensamblar(cfg, raiz, umbral=0.5)
    assert ["geo-a.x@v001", "geo-a.x@v002"] in r["manifest"]["grupos_near_duplicates"]
    refs = [l["ref"] for l in _lineas(os.path.join(r["ruta"], "train.jsonl"))]
    assert refs == ["geo-a.x@v001", "geo-a.x@v002"]


def test_t09_122_fichero_por_encima_del_tope_se_omite_sin_leerlo(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz, escribir=False, tope_fichero=2048)
    assert all(c["particion"] for c in r["manifest"]["casos"] if c["ref"] in ("geo-a.x@v001", "geo-a.x@v002"))
    tr = _gold_ruta(store, "a.x", 1) / "trajectory.jsonl"
    with open(tr, "ab") as f:
        f.write(b" " * 4096)
    r = _ensamblar(cfg, raiz, escribir=False, tope_fichero=2048)
    c = {c["ref"]: c for c in r["manifest"]["casos"]}["geo-a.x@v001"]
    assert c["particion"] is None and "tope" in c["motivo"] and "trajectory.jsonl" in c["motivo"]


def test_t09_122_hash_de_un_fichero_del_export_en_streaming(tmp_path):
    """Comparar un export ajeno (p. ej. un `manifest.json` plantado de 8 MiB) no lo carga entero."""
    d = tmp_path / "e"
    d.mkdir()
    (d / "manifest.json").write_bytes(b"x" * (8 * 1024 * 1024))
    tracemalloc.start()
    sha = asm._sha_fichero(str(d), "manifest.json")
    pico = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert sha == hashlib.sha256(b"x" * (8 * 1024 * 1024)).hexdigest()
    assert pico < 1024 * 1024, pico


def test_t09_123_motivo_sin_rutas_absolutas_ni_errores_del_sistema(tmp_path, monkeypatch):
    """#123 (CWE-209): el `OSError` (con la ruta absoluta del store) nunca llega a `manifest.json`."""
    raiz, cfg, store = _store_basico(tmp_path)
    real = rec._leer_json_reintentando
    victima = str(_gold_ruta(store, "a.x", 1) / "request.json")

    def lector(ruta, *a, **k):
        if os.path.normcase(os.path.abspath(ruta)) == os.path.normcase(os.path.abspath(victima)):
            raise PermissionError(13, "Permission denied", os.path.abspath(ruta))
        return real(ruta, *a, **k)
    monkeypatch.setattr(rec, "_leer_json_reintentando", lector)
    r = _ensamblar(cfg, raiz)
    texto = open(os.path.join(r["ruta"], "manifest.json"), encoding="utf-8").read()
    c = {c["ref"]: c for c in json.loads(texto)["casos"]}["geo-a.x@v001"]
    assert c["particion"] is None and "request.json" in c["motivo"] and "omitida" in c["motivo"]
    for fuga in ("Errno", "WinError", "Permission denied", str(tmp_path), json.dumps(str(tmp_path))[1:-1]):
        assert fuga not in texto, fuga


def _ensamblador_proceso(raiz):
    return subprocess.Popen([sys.executable, os.path.join(HERE, "dataset-assembler.py"), "--project-root", raiz,
                             "--benchmark", "bench", "--fecha", FECHA], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, encoding="utf-8")


def test_t09_124_dos_ensambladores_a_la_vez_no_duplican_el_export(tmp_path):
    """#124: 6 procesos reales a la vez -> UN export (el resto: «ya existe»), nunca `.2`, `.3`…"""
    raiz, cfg, store = _store_basico(tmp_path)
    procs = [_ensamblador_proceso(raiz) for _ in range(6)]
    salidas = [p.communicate(timeout=120) for p in procs]
    assert [p.returncode for p in procs] == [0] * 6, salidas
    assert len(_exports(store)) == 1, _exports(store)
    escritos = sum(" escrito: " in o for o, _e in salidas)
    existentes = sum("ya existe" in o for o, _e in salidas)
    assert (escritos, existentes) == (1, 5), salidas


def test_t09_124_la_comprobacion_y_la_creacion_van_bajo_el_bloqueo(tmp_path, monkeypatch):
    raiz, cfg, store = _store_basico(tmp_path)
    dentro = []
    real_enter, real_exit = rec._Bloqueo.__enter__, rec._Bloqueo.__exit__

    def enter(self):
        dentro.append(os.path.basename(self.ruta))
        return real_enter(self)

    def exit_(self, *a):
        dentro.append("fuera")
        return real_exit(self, *a)
    real_mkdir = os.mkdir

    def mkdir(ruta, *a, **k):
        if os.path.basename(os.path.dirname(str(ruta))) == "exports":
            assert dentro and dentro[-1] == ".lock", dentro
        return real_mkdir(ruta, *a, **k)
    monkeypatch.setattr(rec._Bloqueo, "__enter__", enter)
    monkeypatch.setattr(rec._Bloqueo, "__exit__", exit_)
    monkeypatch.setattr(os, "mkdir", mkdir)
    _ensamblar(cfg, raiz)
    assert ".lock" in dentro and dentro[-1] == "fuera"


def test_t09_125_publicar_manifest_verifica_despues(tmp_path, monkeypatch):
    """#125/#133: la comprobacion POSTERIOR del manifiesto (un segundo nombre plantado tras publicarlo)."""
    raiz, cfg, store = _store_basico(tmp_path)
    real = rec._enlazar_sin_sobrescribir

    def publicar_y_enlazar(origen, destino):
        real(origen, destino)
        if os.path.basename(destino) == "manifest.json":
            try:
                os.link(destino, destino + ".segundo-nombre")
            except OSError as e:   # pragma: no cover - entorno
                pytest.skip(f"sin enlaces duros: {e}")
    monkeypatch.setattr(rec, "_enlazar_sin_sobrescribir", publicar_y_enlazar)
    with pytest.raises(asm.Rechazo) as e:
        _ensamblar(cfg, raiz)
    assert "manifest.json" in str(e.value)


def test_t09_125_el_esquema_se_valida_con_la_config_del_proyecto(tmp_path):
    """#125: `validar_caso(caso, config)` (no `None`): una familia que el patron DEL PROYECTO no admite
    (aunque el de por defecto si) no se exporta."""
    raiz, cfg, store = _store_basico(tmp_path)
    estricta = dict(cfg, ids={"family_pattern": "(bench|b)"})
    r = asm.ensamblar(estricta, raiz, {"bench"}, fecha=FECHA, escribir=False)
    c = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert c["geo-a.x@v001"]["particion"] is None and "esquema" in c["geo-a.x@v001"]["motivo"]
    assert c["geo-bench.x@v001"]["particion"] == "benchmark"


def test_t09_125_metadata_que_no_casa_con_su_ruta_se_omite(tmp_path, monkeypatch):
    """#125: tras el recorrido, `metadata.json` de v002 pasa a decir `version: 7` (esquema valido): la
    comprobacion «metadata casa con su ruta» de `leer_caso` lo omite."""
    raiz, cfg, store = _store_basico(tmp_path)
    meta = _gold_ruta(store, "a.x", 2) / "metadata.json"
    real = rec._estado_de_cases

    def recorrido_y_cambio(*a, **k):
        salida = real(*a, **k)
        m = json.loads(meta.read_text(encoding="utf-8"))
        m["version"] = 7
        meta.write_text(json.dumps(m), encoding="utf-8")
        return salida
    monkeypatch.setattr(rec, "_estado_de_cases", recorrido_y_cambio)
    r = _ensamblar(cfg, raiz, escribir=False)
    c = {c["ref"]: c for c in r["manifest"]["casos"]}["geo-a.x@v002"]
    assert c["particion"] is None and "no casa con su ruta" in c["motivo"]


def test_t09_130_metadata_y_validation_se_abren_una_vez_por_version_gold(tmp_path, monkeypatch):
    """#130: lo leido en el recorrido (con su identidad `fstat`) se reutiliza en `leer_caso`."""
    raiz, cfg, store = _store_basico(tmp_path)
    abiertos = []
    real = rec._leer_json_reintentando

    def lector(ruta, *a, **k):
        abiertos.append(ruta)
        return real(ruta, *a, **k)
    monkeypatch.setattr(rec, "_leer_json_reintentando", lector)
    asm.ensamblar(cfg, raiz, {"bench"}, fecha=FECHA, escribir=False)
    v002 = [os.path.basename(p) for p in abiertos if "/a.x/v002/" in p.replace(os.sep, "/")]
    cuenta = {f: v002.count(f) for f in set(v002)}
    # recorrido (metadata + validation) + primera pasada (los otros seis) + segunda pasada (los ocho)
    assert cuenta == {"metadata.json": 2, "validation.json": 2, "request.json": 2, "context.json": 2,
                      "constraints.json": 2, "trajectory.jsonl": 2, "metrics.json": 2, "artifacts.json": 2}, cuenta


def test_t09_130_lo_leido_en_el_recorrido_no_se_reutiliza_si_cambio(tmp_path, monkeypatch):
    raiz, cfg, store = _store_basico(tmp_path)
    val = _gold_ruta(store, "a.x", 2) / "validation.json"
    real = rec._estado_de_cases

    def recorrido_y_cambio(*a, **k):
        salida = real(*a, **k)
        v = json.loads(val.read_text(encoding="utf-8"))
        v["reviewer_note"] = "cambiada tras el recorrido, mismo tamaño?"
        val.write_text(json.dumps(v), encoding="utf-8")
        return salida
    monkeypatch.setattr(rec, "_estado_de_cases", recorrido_y_cambio)
    r = _ensamblar(cfg, raiz, escribir=False)
    c = {c["ref"]: c for c in r["manifest"]["casos"]}["geo-a.x@v002"]
    esperado = hashlib.sha256(val.read_bytes()).hexdigest()
    assert c["ficheros"]["validation.json"] == esperado


def test_t09_131_manifiesto_con_el_nombre_real_del_directorio(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r1 = _ensamblar(cfg, raiz)
    assert _manifest(r1)["directorio"] == r1["export_id"]
    with open(os.path.join(r1["ruta"], "benchmark.jsonl"), "ab") as f:
        f.write(b"{}\n")
    r2 = _ensamblar(cfg, raiz)
    m = _manifest(r2)
    assert os.path.basename(r2["ruta"]) == r1["export_id"] + ".2"
    assert m["export_id"] == r1["export_id"] and m["directorio"] == r1["export_id"] + ".2"


def test_t09_132_gold_cuyo_contenido_cambio_tras_aprobarlo_no_se_exporta(tmp_path):
    """#132: `set-status approved` ata el Gold al contenido (`content_hash`); si un fichero inmutable
    cambia despues, el caso se excluye con motivo."""
    raiz, cfg, store = _store_basico(tmp_path)
    d = _gold_ruta(store, "a.x", 1)
    val = json.loads((d / "validation.json").read_text(encoding="utf-8"))
    assert val["content_hash"] == rec.hash_contenido(
        {f: hashlib.sha256((d / f).read_bytes()).hexdigest() for f in rec.FICHEROS_INMUTABLES})
    (d / "request.json").write_text(json.dumps({"request": "cambiada despues de aprobar"}), encoding="utf-8")
    r = _ensamblar(cfg, raiz, escribir=False)
    c = {c["ref"]: c for c in r["manifest"]["casos"]}["geo-a.x@v001"]
    assert c["particion"] is None and "content_hash" in c["motivo"]
    assert "cambiada despues" not in json.dumps(r["lineas"])


def test_t09_132_gold_sin_hash_de_aprobacion_se_exporta_con_aviso(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    vp = _gold_ruta(store, "a.x", 1) / "validation.json"
    v = json.loads(vp.read_text(encoding="utf-8"))
    del v["content_hash"]
    vp.write_text(json.dumps(v), encoding="utf-8")
    r = _ensamblar(cfg, raiz, escribir=False)
    c = {c["ref"]: c for c in r["manifest"]["casos"]}["geo-a.x@v001"]
    assert c["particion"] == "train"
    assert any("geo-a.x@v001" in a and "sin hash de aprobacion" in a for a in r["manifest"]["avisos"])


def test_t09_133_fichero_en_otro_dispositivo_que_su_version_se_omite(tmp_path, monkeypatch):
    """#133: la guarda de `st_dev` (inyeccion determinista: el `fstat` de `request.json` dice otro
    dispositivo)."""
    raiz, cfg, store = _store_basico(tmp_path)
    real = rec._leer_de_version

    def lector(dir_v, fichero, rel, fstat_leido=None, *a, **k):
        salida = real(dir_v, fichero, rel, fstat_leido, *a, **k)
        if fichero == "request.json" and fstat_leido and "a.x" in dir_v and dir_v.endswith("v001"):
            st = list(fstat_leido[-1])
            st[2] = st[2] + 1
            fstat_leido[-1] = os.stat_result(st)
        return salida
    monkeypatch.setattr(rec, "_leer_de_version", lector)
    r = _ensamblar(cfg, raiz, escribir=False)
    c = {c["ref"]: c for c in r["manifest"]["casos"]}["geo-a.x@v001"]
    assert c["particion"] is None and "otro dispositivo" in c["motivo"]


def test_t09_h5_caso_cambiado_entre_pasadas_aborta_sin_manifiesto(tmp_path, monkeypatch):
    """H5: la segunda pasada relee cada caso y comprueba el sha256 de la primera; si cambio, no se
    publica `manifest.json` (export incompleto reconocible) y no se borra nada."""
    raiz, cfg, store = _store_basico(tmp_path)
    real = asm._segunda_pasada
    d = _gold_ruta(store, "a.x", 2)

    def cambio_y_pasada(*a, **k):
        (d / "metrics.json").write_text(json.dumps({"score": 0.99}), encoding="utf-8")
        return real(*a, **k)
    monkeypatch.setattr(asm, "_segunda_pasada", cambio_y_pasada)
    with pytest.raises(asm.Rechazo) as e:
        _ensamblar(cfg, raiz)
    assert "geo-a.x@v002" in str(e.value) and "entre pasadas" in str(e.value) and "incompleto" in str(e.value)
    (x,) = _exports(store)
    assert "manifest.json" not in os.listdir(store / "exports" / x)


def test_t09_h5_no_guarda_los_casos_ni_los_bytes_del_export(tmp_path):
    """H5: memoria O(n · muestra), nunca O(tamaño de los casos): 20 Gold con un `metrics.json` opaco de
    ~600 KiB (no se shinglea ni se exporta) -> el pico queda por debajo de lo que ocupan en disco (antes,
    los 20 casos leidos vivian en memoria hasta el final)."""
    raiz, cfg, store = _proyecto(tmp_path)
    for i in range(20):
        _grabar(cfg, raiz, family="bench" if i < 2 else "a", variant=f"v{i}", request=f"peticion numero {i} distinta",
                metrics={"serie": [(i * 30000 + k) / 7 for k in range(30000)]})
    total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _d, fs in os.walk(store / "cases") for f in fs)
    tracemalloc.start()
    r = _ensamblar(cfg, raiz)
    pico = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert r["manifest"]["ficheros"]["train.jsonl"]["lineas"] == 18 and r["lineas"] is None
    assert total > 10 * 1024 * 1024 and pico < total / 2, (pico, total)


def test_t09_dry_run_devuelve_lineas_y_el_mismo_manifiesto(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    seco = _ensamblar(cfg, raiz, escribir=False)
    r = _ensamblar(cfg, raiz)
    assert seco["manifest"] == _manifest(r)
    assert [l["ref"] for l in seco["lineas"]["train.jsonl"]] == ["geo-a.x@v001", "geo-a.x@v002"]


# ------------------------------------------------------------------ fix2 de la Fase 3 (#134, #136, #137, #140, #143, #145, #147)

def test_t09_134_metadata_o_validation_por_encima_del_tope_se_omiten_en_el_recorrido(tmp_path):
    """#134 (CWE-400/770): el tope por fichero se aplica TAMBIEN al recorrido del store, que leia
    enteros `metadata.json`/`validation.json` de TODAS las versiones (Gold o no): una version con uno
    de ellos por encima del tope se omite con aviso, sin cargarlo."""
    raiz, cfg, store = _store_basico(tmp_path)
    with open(_gold_ruta(store, "b.x", 1) / "metadata.json", "ab") as f:      # rejected: no Gold
        f.write(b" " * 8192)
    with open(_gold_ruta(store, "b.y", 1) / "validation.json", "ab") as f:    # needs_changes
        f.write(b" " * 8192)
    r = _ensamblar(cfg, raiz, escribir=False, tope_fichero=4096)
    refs = {c["ref"] for c in r["manifest"]["casos"]}
    assert "geo-b.x@v001" not in refs and "geo-b.y@v001" not in refs
    assert "geo-a.x@v001" in refs and "geo-bench.x@v001" in refs
    assert any("b.x" in a and "metadata.json" in a and "tope" in a for a in r["avisos_store"]), r["avisos_store"]
    assert any("b.y" in a and "validation.json" in a and "tope" in a for a in r["avisos_store"]), r["avisos_store"]


def test_t09_147_lo_leido_en_el_recorrido_por_encima_del_tope_no_se_reutiliza(tmp_path):
    """#147: `_reutilizable` descarta lo leido en el recorrido si pasa del tope de la lectura del caso
    (`len(datos) > tope`), aunque el nombre siga siendo el mismo fichero: se relee con el tope y se omite."""
    raiz, cfg, store = _store_basico(tmp_path)
    with open(_gold_ruta(store, "a.x", 1) / "validation.json", "ab") as f:
        f.write(b" " * 3000)
    crudos = {}
    entradas = rec._estado_de_cases(str(store), raiz, crudos=crudos)[0]
    clave = next(k for k, e in entradas.items() if e["family"] == "a" and e["variant"] == "x" and e["version"] == 1)
    assert len(crudos[clave]["validation.json"][0]) > 2048
    width = asm.cs.patrones_id(cfg)[2]
    caso, _h, aviso = asm.leer_caso(rec._Canon(str(store), raiz), str(store), entradas[clave], cfg, width,
                                    crudos[clave], tope=2048)
    assert caso is None and "validation.json" in aviso and "tope" in aviso, aviso


def test_t09_136_140_ventana_del_temporal_del_manifiesto(tmp_path, monkeypatch):
    """#136/#140 (CWE-451/367): `exports/<id>` sustituido por un enlace al arbol curado JUSTO al crear el
    `.tmp-<token>` del manifiesto: se comprueba ANTES de escribir un byte (nada del manifiesto pasa al
    arbol curado) y el aviso solo nombra lo que sigue existiendo (el temporal propio ya se retiro)."""
    raiz, cfg, store = _store_basico(tmp_path)
    curado = tmp_path / "proj" / "docs" / "knowledge" / "approved" / "lessons"
    curado.mkdir(parents=True)
    real_abrir, real_retirar = rec._abrir_exclusivo, rec._retirar_temporal_propio
    tamanos = []

    def abrir(ruta):
        destino = os.path.dirname(ruta)
        if os.path.basename(ruta).startswith(rec.PREFIJO_TEMPORAL) and \
                os.path.basename(os.path.dirname(destino)) == "exports":
            os.rename(destino, destino + ".aparte")
            _enlazar_dir(curado, destino)
        return real_abrir(ruta)

    def retirar(ruta, st):
        try:
            tamanos.append(os.lstat(ruta).st_size)
        except OSError:
            tamanos.append(None)
        return real_retirar(ruta, st)
    monkeypatch.setattr(rec, "_abrir_exclusivo", abrir)
    monkeypatch.setattr(rec, "_retirar_temporal_propio", retirar)
    with pytest.raises(asm.Rechazo) as e:
        _ensamblar(cfg, raiz)
    monkeypatch.undo()
    msg = str(e.value)
    assert tamanos == [0], tamanos                                   # ni un byte del manifiesto
    assert os.listdir(curado) == []                                  # nada queda en el arbol curado
    assert "quedo en" not in msg and "ya se retiro" in msg and "incompleto" in msg, msg
    (aparte,) = [n for n in os.listdir(store / "exports") if n.endswith(".aparte")]
    assert sorted(os.listdir(store / "exports" / aparte)) == ["benchmark.jsonl", "train.jsonl"]   # nada se borra


def test_t09_140_ventana_de_la_publicacion_del_manifiesto(tmp_path, monkeypatch):
    """#140: `exports/<id>` sustituido por un enlace entre la comprobacion del temporal y su publicacion
    como `manifest.json`: la publicacion falla, nada llega al arbol curado y nada se borra."""
    raiz, cfg, store = _store_basico(tmp_path)
    curado = tmp_path / "proj" / "docs" / "knowledge" / "approved" / "lessons"
    curado.mkdir(parents=True)
    real = rec._enlazar_sin_sobrescribir

    def enlazar(origen, destino):
        d = os.path.dirname(destino)
        os.rename(d, d + ".aparte")
        _enlazar_dir(curado, d)
        return real(origen, destino)
    monkeypatch.setattr(rec, "_enlazar_sin_sobrescribir", enlazar)
    with pytest.raises((asm.Rechazo, OSError)) as e:
        _ensamblar(cfg, raiz)
    monkeypatch.undo()
    assert "incompleto" in str(e.value)
    assert os.listdir(curado) == []
    (aparte,) = [n for n in os.listdir(store / "exports") if n.endswith(".aparte")]
    nombres = sorted(os.listdir(store / "exports" / aparte))
    assert nombres[1:] == ["benchmark.jsonl", "train.jsonl"] and nombres[0].startswith(rec.PREFIJO_TEMPORAL)


@pytest.mark.skipif(os.name == "nt", reason=(
    "#140: Windows no deja renombrar un directorio con un fichero abierto (train.jsonl): esa ventana no "
    "existe alli; se demuestra en Linux"))
def test_t09_140_ventana_de_benchmark_jsonl(tmp_path, monkeypatch):
    """#140: `exports/<id>` sustituido por un enlace entre la creacion de `train.jsonl` y la de
    `benchmark.jsonl`: el segundo se comprueba al crearlo, el aviso lo nombra (es el creado, vacio) y
    nada mas fluye; nada se borra."""
    raiz, cfg, store = _store_basico(tmp_path)
    curado = tmp_path / "proj" / "docs" / "knowledge" / "approved" / "lessons"
    curado.mkdir(parents=True)
    real = rec._abrir_exclusivo

    def abrir(ruta):
        if os.path.basename(ruta) == "benchmark.jsonl":
            d = os.path.dirname(ruta)
            os.rename(d, d + ".aparte")
            _enlazar_dir(curado, d)
        return real(ruta)
    monkeypatch.setattr(rec, "_abrir_exclusivo", abrir)
    with pytest.raises(asm.Rechazo) as e:
        _ensamblar(cfg, raiz)
    monkeypatch.undo()
    msg = str(e.value)
    assert "benchmark.jsonl" in msg and "quedo en" in msg and "no borra nada" in msg, msg
    assert os.listdir(curado) == ["benchmark.jsonl"] and (curado / "benchmark.jsonl").stat().st_size == 0
    (aparte,) = [n for n in os.listdir(store / "exports") if n.endswith(".aparte")]
    assert os.listdir(store / "exports" / aparte) == ["train.jsonl"]


def test_t09_137_el_manifiesto_se_redacta(tmp_path):
    """#137 (CWE-312/532): `casos[].motivo` copiaba el `campo` del esquema, que incluye CLAVES de la
    trayectoria: `{"meta": {"ghp_…": {"reasoning": "x"}}}` dejaba el token literal en el manifiesto."""
    raiz, cfg, store = _proyecto(tmp_path)
    r = _grabar(cfg, raiz, gold=False, family="a", variant="x")
    _grabar(cfg, raiz, family="bench", variant="x", request="engranaje de doce dientes")
    secreto = _secretos()[0]
    (_gold_ruta(store, "a.x", 1) / "trajectory.jsonl").write_text(
        json.dumps({"role": "user", "content": "hola", "meta": {secreto: {"reasoning": "x"}}}) + "\n", encoding="utf-8")
    rec.cambiar_estado(r["case_id"], 1, "approved", cfg, raiz, approved_by_human=True)
    out = _ensamblar(cfg, raiz)
    texto = open(os.path.join(out["ruta"], "manifest.json"), encoding="utf-8").read()
    c = {c["ref"]: c for c in _manifest(out)["casos"]}["geo-a.x@v001"]
    assert c["particion"] is None and "esquema" in c["motivo"]
    assert secreto not in texto and rec.REDACTADO in c["motivo"]


def _con_lock_tomado(store, segundos):
    """Un hilo toma `exports/.lock` (otro ensamblador en su pasada 2) durante `segundos`."""
    import threading
    os.makedirs(store / "exports", exist_ok=True)
    tomado, soltar = threading.Event(), threading.Event()

    def retener():
        with rec._Bloqueo(str(store / "exports"), asm.BLOQUEO_EXPORTS):
            tomado.set()
            soltar.wait(segundos)
    h = threading.Thread(target=retener, daemon=True)
    h.start()
    assert tomado.wait(10)
    return h, soltar


def test_t09_143_espera_del_bloqueo_configurable_y_mensaje_de_exit_3(tmp_path):
    """#143: `exports/.lock` ocupado mas que la espera -> exit 3 sin escribir nada, con un mensaje que
    dice que la pasada 1 no deja nada a medias y cuanto esperar (`--espera-bloqueo`, default 120 s)."""
    assert asm.ESPERA_BLOQUEO_EXPORTS_S == 120
    raiz, cfg, store = _store_basico(tmp_path)
    h, soltar = _con_lock_tomado(store, 30)
    try:
        t0 = time.monotonic()
        with pytest.raises(rec.BloqueoNoDisponible) as e:
            _ensamblar(cfg, raiz, espera_bloqueo=0.5)
        assert time.monotonic() - t0 < 5
    finally:
        soltar.set()
        h.join(10)
    msg = str(e.value.mensaje)
    assert "0.5 s" in msg and "--espera-bloqueo" in msg and "no se ha escrito nada" in msg and "pasada 1" in msg, msg
    assert _exports(store) == []


def test_t09_143_con_espera_suficiente_termina_cuando_se_suelta(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    h, soltar = _con_lock_tomado(store, 1.0)
    try:
        r = _ensamblar(cfg, raiz, espera_bloqueo=30)
    finally:
        soltar.set()
        h.join(10)
    assert r["existente"] is False and _exports(store) == [os.path.basename(r["ruta"])]


def test_t09_143_cli_espera_bloqueo(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    p = _cli("--project-root", raiz, "--benchmark", "bench", "--espera-bloqueo", "-1")
    assert p.returncode == 2 and "Traceback" not in p.stderr and "espera" in p.stderr
    h, soltar = _con_lock_tomado(store, 30)
    try:
        p = _cli("--project-root", raiz, "--benchmark", "bench", "--fecha", FECHA, "--espera-bloqueo", "0.3")
    finally:
        soltar.set()
        h.join(10)
    assert p.returncode == 3 and "--espera-bloqueo" in p.stderr and "Traceback" not in p.stderr, p.stderr


def test_t09_145_cruces_conservadores_solo_excluyen_de_train():
    """#145 (b): un par de `cruces` (Jaccard muestreado >= umbral - margen) saca de train al de train y
    conserva el de benchmark; entre dos casos de train no hace nada."""
    casos = [_c("geo-a.x@v001", "a"), _c("geo-a.y@v001", "a"), _c("geo-b.x@v001", "b")]
    r = {c["ref"]: c for c in asm.particionar(casos, {"b"}, cruces=[["geo-a.x@v001", "geo-b.x@v001"],
                                                                     ["geo-a.y@v001", "geo-a.x@v001"]])}
    assert r["geo-a.x@v001"]["particion"] is None and "conservador" in r["geo-a.x@v001"]["motivo"]
    assert "geo-b.x@v001" in r["geo-a.x@v001"]["motivo"]
    assert r["geo-a.y@v001"]["particion"] == "train" and r["geo-b.x@v001"]["particion"] == "benchmark"


def test_t09_145_el_ensamblador_pasa_el_lado_de_benchmark_y_aplica_los_cruces(tmp_path, monkeypatch):
    raiz, cfg, store = _store_basico(tmp_path)
    real = asm.dd.Acumulador.agrupar
    vistos = []

    def agrupar(self, *a, **k):
        vistos.append(k.get("benchmark_ids"))
        r = real(self, *a, **k)
        return dict(r, cruces=[["geo-a.x@v002", "geo-bench.x@v001"]])
    monkeypatch.setattr(asm.dd.Acumulador, "agrupar", agrupar)
    r = _ensamblar(cfg, raiz, escribir=False)
    assert vistos == [{"geo-bench.x@v001"}]
    c = {c["ref"]: c for c in r["manifest"]["casos"]}
    assert c["geo-a.x@v002"]["particion"] is None and "conservador" in c["geo-a.x@v002"]["motivo"]
    assert r["manifest"]["cruces_near_duplicates"] == [["geo-a.x@v002", "geo-bench.x@v001"]]
    assert r["manifest"]["near_duplicates"]["cruce"] == {"criterio": "umbral"}


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason=(
    "#135: FIFO solo en POSIX (Windows no tiene os.mkfifo): se demuestra en Linux"))
def test_t09_135_sha_de_un_fichero_del_export_no_se_bloquea_en_un_fifo(tmp_path, monkeypatch):
    """#135 (CWE-367/400): un `manifest.json` sustituido por un FIFO entre el `lstat` (que vio un
    fichero regular) y la apertura bloqueaba `_sha_fichero` para siempre con `exports/.lock` tomado."""
    import threading
    d = tmp_path / "e"
    d.mkdir()
    regular = tmp_path / "regular.json"
    regular.write_bytes(b"{}")
    os.mkfifo(str(d / "manifest.json"))
    real = rec._stat_sin_seguir
    monkeypatch.setattr(rec, "_stat_sin_seguir", lambda x: real(str(regular)) if str(x).endswith("manifest.json")
                        else real(x))
    salida = {}
    h = threading.Thread(target=lambda: salida.setdefault("r", asm._sha_fichero(str(d), "manifest.json")), daemon=True)
    h.start()
    h.join(3)
    bloqueado = h.is_alive()
    if bloqueado:
        os.close(os.open(str(d / "manifest.json"), os.O_WRONLY | os.O_NONBLOCK))
        h.join(5)
    assert not bloqueado and salida["r"] is None


# ------------------------------------------------------------------ T-10: frescura del dataset para /doctor

def _ns(store, *partes):
    return os.lstat(os.path.join(str(store), *partes)).st_mtime_ns


def test_t10_estado_dataset_sin_gold_no_hay_nada_que_exportar(tmp_path):
    _raiz, _cfg, store = _proyecto(tmp_path)
    d = asm.estado_dataset(str(store), None)
    assert d["estado"] == "sin_gold" and d["exports"] == 0 and d["ultimo"] is None


def test_t10_estado_dataset_con_gold_y_ningun_export_esta_desactualizado(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    d = asm.estado_dataset(str(store), 1)
    assert d["estado"] == "sin_export" and d["exports"] == 0 and "ningun export" in d["motivo"]


def test_t10_estado_dataset_al_dia_y_luego_desactualizado_por_un_gold_nuevo(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz)
    nombre = os.path.basename(r["ruta"])
    m = _ns(store, "exports", nombre, "manifest.json")
    d = asm.estado_dataset(str(store), m - 1)
    assert d["estado"] == "al_dia" and d["exports"] == 1 and d["ultimo"] == nombre
    d = asm.estado_dataset(str(store), m + 1)
    assert d["estado"] == "desactualizado" and d["ultimo"] == nombre and nombre in d["motivo"]


def test_t10_estado_dataset_un_export_sin_manifest_es_incompleto_y_no_cuenta(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    (store / "exports" / "20260101-000000000000").mkdir(parents=True)
    (store / "exports" / "falso").mkdir()
    (store / "exports" / "falso" / "manifest.json").mkdir()          # no es un fichero regular
    d = asm.estado_dataset(str(store), 1)
    assert d["estado"] == "sin_export" and d["exports"] == 0 and d["incompletos"] == 2


def test_t10_estado_dataset_no_sigue_enlaces(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz, escribir=True)
    fuera = tmp_path / "fuera"
    (fuera / "x").mkdir(parents=True)
    (fuera / "x" / "manifest.json").write_text("{}", encoding="utf-8")
    _enlazar_dir(fuera / "x", store / "exports" / "99999999-enlazado")
    os.utime(str(fuera / "x" / "manifest.json"), ns=(4_000_000_000_000_000_000,) * 2)
    d = asm.estado_dataset(str(store), 3_000_000_000_000_000_000)
    assert d["ultimo"] == os.path.basename(r["ruta"]) and d["estado"] == "desactualizado"
    assert d["incompletos"] == 1


def test_t10_estado_dataset_exports_que_es_un_enlace_no_se_sigue(tmp_path):
    _raiz, _cfg, store = _proyecto(tmp_path)
    store.mkdir()
    fuera = tmp_path / "fuera-exports"
    (fuera / "x").mkdir(parents=True)
    (fuera / "x" / "manifest.json").write_text("{}", encoding="utf-8")
    _enlazar_dir(fuera, store / "exports")
    d = asm.estado_dataset(str(store), 1)
    assert d["estado"] == "no_verificable" and d["exports"] == 0 and "enlace" in d["motivo"]


def test_t10_estado_dataset_no_escribe_nada(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    antes = sorted(os.listdir(str(store)))
    asm.estado_dataset(str(store), 1)
    assert sorted(os.listdir(str(store))) == antes and not (store / "exports").exists()
