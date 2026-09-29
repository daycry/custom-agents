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
    """Los exports de `exports/` (sin el `.lock` de la exclusion entre ensambladores, #124, ni la marca
    `.ultimo.json` del ultimo ensamblado, D-f4: ningun nombre que empiece por `.`)."""
    return sorted(n for n in os.listdir(store / "exports") if not n.startswith("."))


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
    assert sorted(os.listdir(store / "exports")) == [".lock", asm.MARCA, os.path.basename(r1["ruta"])]   # D-f4
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
    # fix2 (#171/M6): el tope del RECORRIDO es `TOPE_JSON_CASO` (el mismo de `/doctor`), no `tope_fichero`
    with open(_gold_ruta(store, "b.x", 1) / "metadata.json", "ab") as f:      # rejected: no Gold
        f.write(b" " * (rec.TOPE_JSON_CASO + 1))
    with open(_gold_ruta(store, "b.y", 1) / "validation.json", "ab") as f:    # needs_changes
        f.write(b" " * (rec.TOPE_JSON_CASO + 1))
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

def _vigentes(store, raiz):
    """El resumen del store tal como lo ve `/doctor` (D-f4: su `firma`, `n_gold`, `truncado`…)."""
    return rec.resumen_store(str(store), raiz)


def _viejo(ruta, segundos=3600):
    t = time.time() - segundos
    os.utime(str(ruta), (t, t))


def test_t10_estado_dataset_sin_gold_no_hay_nada_que_exportar(tmp_path):
    _raiz, _cfg, store = _proyecto(tmp_path)
    for gold in (None, {}):
        d = asm.estado_dataset(str(store), gold)
        assert d["estado"] == "sin_gold" and d["exports"] == 0 and d["ultimo"] is None


def test_t10_estado_dataset_con_gold_y_ningun_export_esta_desactualizado(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    d = asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert d["estado"] == "sin_export" and d["exports"] == 0 and "ningun export" in d["motivo"]


def test_t10_estado_dataset_al_dia_y_luego_desactualizado_por_un_gold_nuevo(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz, escribir=True)
    nombre = os.path.basename(r["ruta"])
    d = asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert d["estado"] == "al_dia" and d["exports"] == 1 and d["ultimo"] == nombre
    _grabar(cfg, raiz, family="c", variant="x", request="escalera de caracol con barandilla de hierro forjado")
    d = asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert d["estado"] == "desactualizado" and d["ultimo"] == nombre and nombre in d["motivo"]


def test_t10_estado_dataset_un_export_sin_manifest_es_incompleto_y_no_cuenta(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    (store / "exports" / "20260101-000000000000").mkdir(parents=True)
    (store / "exports" / "falso").mkdir()
    (store / "exports" / "falso" / "manifest.json").mkdir()          # no es un fichero regular
    for n in ("20260101-000000000000", "falso"):
        _viejo(store / "exports" / n)
    d = asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert d["estado"] == "sin_export" and d["exports"] == 0 and d["incompletos"] == 2
    assert d["en_curso"] == 0 and d["otros"] == 0


def test_t10_estado_dataset_no_sigue_enlaces(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz, escribir=True)
    fuera = tmp_path / "fuera"
    (fuera / "x").mkdir(parents=True)
    (fuera / "x" / "manifest.json").write_text('{"casos": []}', encoding="utf-8")
    _enlazar_dir(fuera / "x", store / "exports" / "99999999-enlazado")
    os.utime(str(fuera / "x" / "manifest.json"), ns=(4_000_000_000_000_000_000,) * 2)
    d = asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert d["ultimo"] == os.path.basename(r["ruta"]) and d["estado"] == "al_dia"
    assert d["otros"] == 1 and d["incompletos"] == 0


def test_t10_estado_dataset_exports_que_es_un_enlace_no_se_sigue(tmp_path):
    _raiz, _cfg, store = _proyecto(tmp_path)
    store.mkdir()
    fuera = tmp_path / "fuera-exports"
    (fuera / "x").mkdir(parents=True)
    (fuera / "x" / "manifest.json").write_text("{}", encoding="utf-8")
    _enlazar_dir(fuera, store / "exports")
    d = asm.estado_dataset(str(store), {"n_gold": 1, "firma": "0" * 64})
    assert d["estado"] == "no_verificable" and d["exports"] == 0 and "enlace" in d["motivo"]


def test_t10_estado_dataset_no_escribe_nada(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    antes = sorted(os.listdir(str(store)))
    asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert sorted(os.listdir(str(store))) == antes and not (store / "exports").exists()


# ------------------------------------------------------------------ T-10 fix1 (revision intento 1, Fase 4)

def test_t10fix1_154_frescura_por_contenido_no_por_mtime(tmp_path):
    """#154: re-aprobar un Gold ya aprobado (o un `touch`) no deja el dataset «desactualizado»; y
    reensamblar el mismo dia («ya existe», sin escribir) no lo deja asi para siempre. Un Gold que
    DEJA de serlo tras exportar si lo desactualiza (antes era un limite declarado)."""
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz, escribir=True)
    val = store / "cases" / "a.x" / "v001" / "validation.json"
    os.utime(str(val), ns=(4_000_000_000_000_000_000,) * 2)                            # `touch`
    d = asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert d["estado"] == "al_dia", d
    r2 = _ensamblar(cfg, raiz, escribir=True)                                          # «ya existe»
    assert r2["existente"] is True and r2["ruta"] == r["ruta"]
    assert asm.estado_dataset(str(store), _vigentes(store, raiz))["estado"] == "al_dia"
    rec.cambiar_estado("geo-a.x", 1, "approved", cfg, raiz, approved_by_human=True)     # re-aprobar
    os.utime(str(val), ns=(4_000_000_000_000_000_000,) * 2)
    assert asm.estado_dataset(str(store), _vigentes(store, raiz))["estado"] == "al_dia"
    rec.cambiar_estado("geo-a.x", 2, "rejected", cfg, raiz)                            # deja de ser Gold
    d = asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert d["estado"] == "desactualizado" and "2 Gold vigentes frente a 3" in d["motivo"], d


def test_t10fix1_154_un_gold_cuyo_contenido_cambio_desactualiza(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    res = _vigentes(store, raiz)
    gold = dict(res["gold"])
    clave = sorted(k for k, h in gold.items() if h)[0]
    gold[clave] = "0" * 64                                     # D-f4: la firma de otro contenido aprobado
    d = asm.estado_dataset(str(store), dict(res, gold=gold, firma=rec.firma_gold(gold)))
    assert d["estado"] == "desactualizado" and "contenido distinto" in d["motivo"], d


def test_t10fix1_154_con_recuento_parcial_solo_se_comprueba_lo_recorrido(tmp_path):
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    res = _vigentes(store, raiz)
    parte = dict([sorted(res["gold"].items())[0]])                # D-f4 + M10: lo recorrido, sin cortar ni no
    parcial = dict(res, gold=parte, n_gold=1, firma=rec.firma_gold(parte), truncado=True)
    assert asm.estado_dataset(str(store), parcial)["estado"] == "parcial"
    assert asm.estado_dataset(str(store), dict(parcial, truncado=False))["estado"] == "desactualizado"


def test_t10fix1_156_en_curso_incompleto_y_otros_son_categorias_distintas(tmp_path):
    """#156: un fichero suelto en `exports/` no es un «export incompleto», ni lo es el directorio de un
    export EN CURSO (reciente, o con `exports/.lock` tomado por otro ensamblador)."""
    raiz, cfg, store = _store_basico(tmp_path)
    ex = store / "exports"
    (ex / "20260101-aaaaaaaaaaaa").mkdir(parents=True)                # en curso: recien creado
    (ex / "20250101-bbbbbbbbbbbb").mkdir()                            # incompleto: viejo, sin manifest
    _viejo(ex / "20250101-bbbbbbbbbbbb")
    (ex / "notas.txt").write_text("x", encoding="utf-8")              # otros: no es un export
    d = asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert (d["en_curso"], d["incompletos"], d["otros"]) == (1, 1, 1), d
    _viejo(ex / "20260101-aaaaaaaaaaaa", 1800)                        # viejo, pero con el bloqueo tomado:
    with rec._Bloqueo(str(ex), asm.BLOQUEO_EXPORTS):                  # el mas reciente sigue en curso
        d = asm.estado_dataset(str(store), _vigentes(store, raiz))
    assert (d["en_curso"], d["incompletos"], d["otros"]) == (1, 1, 1), d
    d = asm.estado_dataset(str(store), _vigentes(store, raiz))        # bloqueo liberado: incompleto
    assert (d["en_curso"], d["incompletos"], d["otros"]) == (0, 2, 1), d


def test_t10fix1_152_el_recorrido_de_exports_va_dentro_del_plazo(tmp_path):
    """#152 (CWE-400): con el plazo agotado, `exports/` no se recorre: «no verificado (PARCIAL)»."""
    raiz, cfg, store = _store_basico(tmp_path)
    for i in range(30):
        (store / "exports" / f"2026010{i % 9}-{i:012d}").mkdir(parents=True)
    d = asm.estado_dataset(str(store), _vigentes(store, raiz), hasta=rec._crono() - 1)
    assert d["estado"] == "parcial" and "tope de tiempo" in d["motivo"] and d["exports"] == 0, d


# ------------------------------------------------------------------ T-10 fix2: D-f4 (firma de la entrada + marca del ultimo ensamblado)

def _estado(store, raiz, **kw):
    return asm.estado_dataset(str(store), rec.resumen_store(str(store), raiz), **kw)


def _marca(store):
    with open(str(store / "exports" / asm.MARCA), encoding="utf-8") as f:
        return json.load(f)


def test_t10fix2_f2_el_ensamblado_real_escribe_la_marca_del_ultimo_ensamblado(tmp_path):
    """F2 + M3 + M6: tras un ensamblado REAL («escrito» o «ya existe»), `exports/.ultimo.json` =
    `{version, export_id, directorio, firma, gold, creado, parametros}` (<= 4 KiB): la firma es la de la
    entrada que ve `/doctor` y `--dry-run` no la escribe."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=False)
    assert not (store / "exports").exists()
    r = _ensamblar(cfg, raiz, escribir=True)
    m = _marca(store)
    assert sorted(m) == sorted(asm.CLAVES_MARCA) and m["version"] == 1
    assert m["directorio"] == os.path.basename(r["ruta"]) == m["export_id"] == r["export_id"]
    res = rec.resumen_store(str(store), raiz)
    assert m["firma"] == res["firma"] and m["gold"] == res["n_gold"] == 3
    assert m["parametros"]["benchmark"] == ["bench"] and m["parametros"]["umbral"] == 0.8
    assert (store / "exports" / asm.MARCA).stat().st_size <= asm.TOPE_MARCA
    assert r["aviso_marca"] is None
    d = _estado(store, raiz)
    assert d["estado"] == "al_dia" and d["ultimo"] == m["directorio"], d
    assert "con los parametros del ultimo ensamblado" in d["motivo"] and "benchmark=bench" in d["motivo"]


def test_t10fix2_168_b21_sin_atar_reaprobar_desactualiza_y_reensamblar_limpia(tmp_path):
    """#168 (B2-1 literal): se cambia `request.json` de un Gold -> el export lo excluye («sin atar») ->
    se re-aprueba (el remedio del propio motivo) -> `/doctor` dice `desactualizado` (antes: `al_dia`,
    y reensamblar escribia un export nuevo con ese caso en train) -> reensamblar -> `al_dia`."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    req = store / "cases" / "a.x" / "v001" / "request.json"
    req.write_text(json.dumps({"request": "rampa de treinta grados con bola AZUL"}), encoding="utf-8")
    r1 = _ensamblar(cfg, raiz, escribir=True)
    assert any(c["motivo"] == asm.MOTIVO_SIN_ATAR for c in _manifest(r1)["casos"])
    assert _estado(store, raiz)["estado"] == "al_dia"      # la firma describe la entrada, no el resultado
    rec.cambiar_estado("geo-a.x", 1, "approved", cfg, raiz, approved_by_human=True)
    d = _estado(store, raiz)
    assert d["estado"] == "desactualizado" and "mismo numero de Gold" in d["motivo"], d
    r2 = _ensamblar(cfg, raiz, escribir=True)
    assert r2["existente"] is False and not any(c["motivo"] == asm.MOTIVO_SIN_ATAR for c in _manifest(r2)["casos"])
    assert _estado(store, raiz)["estado"] == "al_dia"


def test_t10fix2_168_nota_a_gold_excluido_por_un_aviso_permanente_sigue_al_dia(tmp_path):
    """#168 (nota de A), con D-f5 (fix3): un Gold que el ensamblador EXCLUYE por un aviso permanente de
    `leer_caso` (trayectoria ilegible) sigue en la firma con su `content_hash` (misma firma: nunca un
    «desactualizado» que reensamblar no limpia) y la marca lo registra como omitido: `con_omisiones`
    (O3), y reensamblar («ya existe») lo deja `con_omisiones` (O4: veredicto cierto sin corregir)."""
    raiz, cfg, store = _store_basico(tmp_path)
    (store / "cases" / "a.x" / "v001" / "trajectory.jsonl").write_text("{roto\n", encoding="utf-8")
    r = _ensamblar(cfg, raiz, escribir=True)
    assert any(c["ref"] == "geo-a.x@v001" and c["particion"] is None for c in _manifest(r)["casos"])
    assert _marca(store)["firma"] == _vigentes(store, raiz)["firma"]
    assert _estado(store, raiz)["estado"] == "con_omisiones"
    r2 = _ensamblar(cfg, raiz, escribir=True)
    assert r2["existente"] is True and _estado(store, raiz)["estado"] == "con_omisiones"


def test_t10fix2_169_b22_ya_existe_reescribe_la_marca_nunca_por_mtime(tmp_path, monkeypatch):
    """#169 (B2-2 literal): E1 -> se rechaza un Gold -> E2 -> se re-aprueba -> reensamblar da E1
    «ya existe» -> `al_dia` (la marca se reescribe tambien en «ya existe»; el ultimo export ya no se
    elige por el `mtime` de su `manifest.json`)."""
    monkeypatch.setattr(rec, "_ahora", lambda: "2026-09-29T10:00:00Z")    # re-aprobar da los mismos bytes
    raiz, cfg, store = _store_basico(tmp_path)
    e1 = _ensamblar(cfg, raiz, escribir=True)
    rec.cambiar_estado("geo-a.x", 2, "rejected", cfg, raiz)
    e2 = _ensamblar(cfg, raiz, escribir=True)
    assert e2["export_id"] != e1["export_id"] and _marca(store)["directorio"] == e2["export_id"]
    rec.cambiar_estado("geo-a.x", 2, "approved", cfg, raiz, approved_by_human=True)
    d = _estado(store, raiz)
    assert d["estado"] == "desactualizado" and "3 Gold vigentes frente a 2" in d["motivo"], d
    e3 = _ensamblar(cfg, raiz, escribir=True)
    assert e3["existente"] is True and e3["export_id"] == e1["export_id"]
    assert _marca(store)["directorio"] == e1["export_id"]
    d = _estado(store, raiz)
    assert d["estado"] == "al_dia" and d["ultimo"] == e1["export_id"], d


def test_t10fix2_m1_una_version_incompleta_vieja_no_deja_la_frescura_sin_verificar(tmp_path):
    """M1 (G1): una omision PERMANENTE (version incompleta vieja) es la misma en los dos lados
    (`_estado_de_cases`): se compara con normalidad -> `al_dia`, nunca `no_verificable` para siempre."""
    raiz, cfg, store = _store_basico(tmp_path)
    (store / "cases" / "a.x" / "v009").mkdir()
    _viejo(store / "cases" / "a.x" / "v009")
    _ensamblar(cfg, raiz, escribir=True)
    res = rec.resumen_store(str(store), raiz)
    assert res["incompletas"] == 1 and res["transitorias"] == 0
    assert asm.estado_dataset(str(store), res)["estado"] == "al_dia"


def test_t10fix2_m2_un_gold_omitido_por_una_causa_transitoria_desactualiza_y_reensamblar_limpia(tmp_path, monkeypatch):
    """M2 (G2), sustituido por D-f5 O1-O3 (fix3): un Gold que `leer_caso` omite por una causa
    TRANSITORIA («no legible tras N reintentos») sigue en la firma con su `content_hash` y la marca lo
    registra como omitido (clase `transitorio`) -> `con_omisiones` (nunca el `al_dia` falso de G2, con
    train 0 frente a 1); reensamblar sin el bloqueo lo limpia -> `al_dia`."""
    monkeypatch.setattr(rec, "_PERMISOS_PERMANENTES", False)               # N6: la causa transitoria de Windows
    raiz, cfg, store = _store_basico(tmp_path)
    real = rec._abrir_lectura
    bloqueada = os.path.normcase(str(store / "cases" / "a.x" / "v002" / "request.json"))

    def bloqueado(ruta):
        if os.path.normcase(str(ruta)) == bloqueada:
            raise PermissionError(13, "bloqueado por otro proceso")
        return real(ruta)
    monkeypatch.setattr(rec, "_abrir_lectura", bloqueado)
    monkeypatch.setattr(rec, "ESPERA_REINTENTO_S", 0.0)
    r = _ensamblar(cfg, raiz, escribir=True)
    assert any(c["ref"] == "geo-a.x@v002" and c["particion"] is None for c in _manifest(r)["casos"])
    monkeypatch.setattr(rec, "_abrir_lectura", real)
    assert _marca(store)["omitidos_muestra"] == [{"ref": "geo-a.x@v002", "clase": "transitorio",
                                                  "causa": "sin permisos o bloqueado"}]
    d = _estado(store, raiz)
    assert d["estado"] == "con_omisiones" and "basta con reensamblar" in d["motivo"], d
    r2 = _ensamblar(cfg, raiz, escribir=True)
    assert r2["existente"] is False and _estado(store, raiz)["estado"] == "al_dia"


def test_t10fix2_m3_la_marca_guarda_el_directorio_real_con_su_sufijo(tmp_path):
    """M3 (G3): `exports/<id>/` incompleto -> el ensamblado escribe `<id>.2`; la marca guarda ESE
    directorio (validado con el patron) -> `al_dia`; reensamblar -> «ya existe» `<id>.2` -> `al_dia`."""
    raiz, cfg, store = _store_basico(tmp_path)
    export_id = _ensamblar(cfg, raiz, escribir=False)["export_id"]
    (store / "exports" / export_id).mkdir(parents=True)
    r = _ensamblar(cfg, raiz, escribir=True)
    assert os.path.basename(r["ruta"]) == f"{export_id}.2"
    m = _marca(store)
    assert m["export_id"] == export_id and m["directorio"] == f"{export_id}.2"
    assert _estado(store, raiz)["estado"] == "al_dia"
    r2 = _ensamblar(cfg, raiz, escribir=True)
    assert r2["existente"] is True and os.path.basename(r2["ruta"]) == f"{export_id}.2"
    d = _estado(store, raiz)
    assert d["estado"] == "al_dia" and d["ultimo"] == f"{export_id}.2", d
    for malo in (f"{export_id}.1", f"{export_id}.100", f"{export_id}/../x", "20260101-ABCDEFABCDEF"):
        assert not asm.PATRON_DIRECTORIO.fullmatch(malo), malo


def test_t10fix2_m4_aba_la_firma_usa_la_lectura_que_decidio_el_destino(tmp_path, monkeypatch):
    """M4 (G4): aprobada (H) en el recorrido -> rechazada DURANTE la pasada 1 (antes de `leer_caso`) ->
    re-aprobada (H). La firma del ensamblado usa la lectura que decidio su destino (`leer_caso`: ya no
    era Gold, sin entrada): tras re-aprobar, `desactualizado` (no un `al_dia` falso)."""
    raiz, cfg, store = _store_basico(tmp_path)
    real = asm.leer_caso

    def leer(ctx, st, entrada, *a, **k):
        if (entrada["case_id"], entrada["version"]) == ("geo-a.x", 1):
            rec.cambiar_estado("geo-a.x", 1, "rejected", cfg, raiz)
        return real(ctx, st, entrada, *a, **k)
    monkeypatch.setattr(asm, "leer_caso", leer)
    r = _ensamblar(cfg, raiz, escribir=True)
    monkeypatch.setattr(asm, "leer_caso", real)
    assert not any(c["ref"] == "geo-a.x@v001" and c["particion"] for c in _manifest(r)["casos"])
    assert _marca(store)["gold"] == 2
    rec.cambiar_estado("geo-a.x", 1, "approved", cfg, raiz, approved_by_human=True)
    d = _estado(store, raiz)
    assert d["estado"] == "desactualizado" and "3 Gold vigentes frente a 2" in d["motivo"], d


def test_t10fix2_m5_un_gold_con_hash_invalido_es_el_mismo_centinela_en_los_dos_lados(tmp_path):
    """M5: un `content_hash` de 1 MB (no es un sha256) cuenta como el centinela `"!"` en `/doctor` y
    en la pasada 1: las firmas coinciden (`al_dia`) sin retener la cadena."""
    raiz, cfg, store = _store_basico(tmp_path)
    val = store / "cases" / "a.x" / "v001" / "validation.json"
    v = json.loads(val.read_text(encoding="utf-8"))
    v["content_hash"] = "x" * 1_000_000
    val.write_text(json.dumps(v), encoding="utf-8")
    r = _ensamblar(cfg, raiz, escribir=True)
    assert any(c["ref"] == "geo-a.x@v001" and c["motivo"] == asm.MOTIVO_SIN_ATAR for c in _manifest(r)["casos"])
    res = rec.resumen_store(str(store), raiz)
    assert res["gold"][("geo-a.x", 1)] is rec.CENTINELA_HASH
    assert asm.estado_dataset(str(store), res)["estado"] == "al_dia"


def test_t10fix2_171_el_ensamblador_aplica_el_mismo_tope_json_caso_que_doctor(tmp_path):
    """#171: el ensamblador lee `metadata.json`/`validation.json` con `TOPE_JSON_CASO` (no con
    `tope_fichero`): un `validation.json` de 1 MiB + 1 omite la version en los DOS lados (misma
    firma, `al_dia`) y uno de 1 MiB se lee aunque `tope_fichero` sea menor."""
    raiz, cfg, store = _store_basico(tmp_path)
    for fv, tam in (("a.x/v001", rec.TOPE_JSON_CASO + 1), ("a.x/v002", 2 * 1024)):
        val = store / "cases" / fv / "validation.json"
        datos = val.read_bytes().rstrip()
        val.write_bytes(datos + b" " * (tam - len(datos)))
    r = _ensamblar(cfg, raiz, escribir=True, tope_fichero=1024 * 1024 + 4096)
    refs = {c["ref"]: c for c in _manifest(r)["casos"]}
    assert "geo-a.x@v001" not in refs and refs["geo-a.x@v002"]["particion"] == "train", refs
    res = rec.resumen_store(str(store), raiz)
    assert res["grandes"] == 1 and asm.estado_dataset(str(store), res)["estado"] == "al_dia"
    (tmp_path / "otro").mkdir()
    raiz2, cfg2, store2 = _store_basico(tmp_path / "otro")           # validation.json entre tope_fichero y 1 MiB:
    val = store2 / "cases" / "a.x" / "v002" / "validation.json"      # `leer_caso` lo omite (grande, permanente)
    datos = val.read_bytes().rstrip()                                # y la firma usa la lectura del recorrido
    val.write_bytes(datos + b" " * (4096 - len(datos)))
    r2 = _ensamblar(cfg2, raiz2, escribir=True, tope_fichero=2048)
    assert any(c["ref"] == "geo-a.x@v002" and c["particion"] is None for c in _manifest(r2)["casos"])
    assert _marca(store2)["firma"] == rec.resumen_store(str(store2), raiz2)["firma"]
    assert _estado(store2, raiz2)["estado"] == "con_omisiones"             # D-f5 (fix3): omision registrada
    assert _marca(store2)["omitidos_muestra"][0]["causa"] == "ilegible"


def _plantar_enlace_fichero(objetivo, enlace):
    try:
        os.symlink(str(objetivo), str(enlace))
    except (OSError, NotImplementedError) as e:          # pragma: no cover - Windows sin privilegio
        return str(e)
    return None


def test_t10fix2_m8_una_marca_ajena_no_se_reemplaza_ni_se_sigue(tmp_path):
    """F2 + M8: una `exports/.ultimo.json` que no es de la pieza (enlace duro, symlink, fichero de
    1 MiB, JSON sin el esquema) NO se reemplaza ni se sigue: el export es valido (aviso con el
    remedio) y la frescura sale `no_verificable` con «retira `exports/.ultimo.json` a mano»."""
    fuera = tmp_path / "ajeno.json"
    casos = []
    for tipo in ("duro", "symlink", "grande", "esquema"):
        (tmp_path / tipo).mkdir()
        raiz, cfg, store = _store_basico(tmp_path / tipo)
        (store / "exports").mkdir(parents=True)
        marca = store / "exports" / asm.MARCA
        fuera.write_text('{"ajeno": true}', encoding="utf-8")
        if tipo == "duro":
            os.link(str(fuera), str(marca))
        elif tipo == "symlink":
            error = _plantar_enlace_fichero(fuera, marca)
            if error:
                casos.append(("symlink omitido", error))
                continue
        elif tipo == "grande":
            with open(str(marca), "wb") as f:
                f.truncate(1024 * 1024)
        else:
            marca.write_text('{"version": 1, "export_id": "x"}', encoding="utf-8")
        antes = (fuera.read_bytes(), os.lstat(str(marca)).st_size)
        creados, real = [], rec._abrir_exclusivo

        def abrir(ruta):                                    # ni siquiera se crea el temporal de la marca
            if os.path.normcase(os.path.dirname(str(ruta))) == os.path.normcase(str(store / "exports")):
                creados.append(os.path.basename(str(ruta)))
            return real(ruta)
        rec._abrir_exclusivo = abrir
        try:
            r = _ensamblar(cfg, raiz, escribir=True)
        finally:
            rec._abrir_exclusivo = real
        assert creados == [], (tipo, creados)
        assert r["ruta"] and r["aviso_marca"] and asm.MARCA in r["aviso_marca"], (tipo, r["aviso_marca"])
        assert (fuera.read_bytes(), os.lstat(str(marca)).st_size) == antes, tipo
        d = _estado(store, raiz)
        assert d["estado"] == "no_verificable" and "a mano (solo ese nombre)" in d["motivo"], (tipo, d)
        casos.append((tipo, "ok"))
    assert [c for c in casos if c[1] == "ok"], casos


def test_t10fix2_m8_la_marca_se_publica_con_reemplazar_y_su_temporal_se_retira(tmp_path, monkeypatch):
    """M8: la marca se publica con `rec._reemplazar` (reintentos acotados) desde un `.tmp-*` propio que
    se retira en un `finally`; si no se puede publicar tras un export valido: aviso y la marca
    anterior intacta (el siguiente ensamblado, «ya existe», la reescribe)."""
    raiz, cfg, store = _store_basico(tmp_path)
    usados = []
    real = rec._reemplazar

    def espia(origen, destino):
        usados.append((os.path.basename(origen)[:5], os.path.basename(destino)))
        return real(origen, destino)
    monkeypatch.setattr(rec, "_reemplazar", espia)
    _ensamblar(cfg, raiz, escribir=True)
    assert usados == [(rec.PREFIJO_TEMPORAL, asm.MARCA)], usados
    anterior = (store / "exports" / asm.MARCA).read_bytes()
    monkeypatch.setattr(rec, "_reemplazar", real)
    _grabar(cfg, raiz, family="c", variant="x", request="escalera de caracol con barandilla de hierro forjado")

    def falla(origen, destino):
        raise PermissionError(13, "bloqueado")
    monkeypatch.setattr(rec, "_reemplazar", falla)
    r = _ensamblar(cfg, raiz, escribir=True)
    assert r["existente"] is False and r["aviso_marca"] and "bloqueada por otro proceso" in r["aviso_marca"]
    assert "el siguiente ensamblado la reescribe" in r["aviso_marca"] and asm.REMEDIO_MARCA not in r["aviso_marca"]
    assert (store / "exports" / asm.MARCA).read_bytes() == anterior
    assert not [n for n in os.listdir(str(store / "exports")) if n.startswith(rec.PREFIJO_TEMPORAL)]
    assert _estado(store, raiz)["estado"] == "desactualizado"
    monkeypatch.setattr(rec, "_reemplazar", real)
    r2 = _ensamblar(cfg, raiz, escribir=True)
    assert r2["existente"] is True and _estado(store, raiz)["estado"] == "al_dia"


def test_t10fix2_m8_muerte_a_mitad_deja_la_marca_anterior_intacta(tmp_path, monkeypatch):
    """F2: una muerte entre el `.tmp` y el reemplazo deja la marca ANTERIOR intacta; un `.tmp-*`
    huerfano en `exports/` no cuenta como export ni estorba al siguiente ensamblado."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    anterior = (store / "exports" / asm.MARCA).read_bytes()

    _grabar(cfg, raiz, family="c", variant="x", request="escalera de caracol con barandilla de hierro forjado")

    def muere(origen, destino):
        raise KeyboardInterrupt
    monkeypatch.setattr(rec, "_reemplazar", muere)
    with pytest.raises(KeyboardInterrupt):
        _ensamblar(cfg, raiz, escribir=True)
    assert (store / "exports" / asm.MARCA).read_bytes() == anterior
    (store / "exports" / f"{rec.PREFIJO_TEMPORAL}deadbeef").write_bytes(b'{"medio')      # muerte «de verdad»
    d = _estado(store, raiz)
    assert d["estado"] == "desactualizado" and d["otros"] == 0 and d["exports"] == 2, d
    monkeypatch.undo()
    _ensamblar(cfg, raiz, escribir=True)
    assert _estado(store, raiz)["estado"] == "al_dia"


def test_t10fix2_m6_los_parametros_no_entran_en_la_firma(tmp_path):
    """M6 (G6): los parametros del ensamblado NO entran en la firma (`/doctor` no sabe con cuales se
    ensamblara): `al_dia` = «mismo train/benchmark con los parametros del ultimo ensamblado»; la marca
    los guarda a titulo informativo."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    f1 = _marca(store)["firma"]
    _ensamblar(cfg, raiz, escribir=True, umbral=0.5, conservar_duplicados=True)
    m = _marca(store)
    assert m["firma"] == f1 and m["parametros"]["umbral"] == 0.5 and m["parametros"]["conservar_duplicados"] is True
    d = _estado(store, raiz)
    assert d["estado"] == "al_dia" and "umbral=0.5" in d["motivo"] and d["parametros"] == m["parametros"]


def test_t10fix2_m10_parcial_con_mas_gold_de_los_de_la_marca_es_desactualizado(tmp_path):
    """M10: con el recuento cortado, si los Gold YA contados superan los de la marca ->
    `desactualizado` (cierto: lo contado es un subconjunto del recorrido completo); si no, «no
    verificado (PARCIAL)» y el remedio `dataset-assembler.py --estado` con el umbral medido."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    res = rec.resumen_store(str(store), raiz)
    d = asm.estado_dataset(str(store), dict(res, truncado=True, n_gold=res["n_gold"] + 1, firma="0" * 64))
    assert d["estado"] == "desactualizado" and "al menos 4 Gold" in d["motivo"], d
    d = asm.estado_dataset(str(store), dict(res, truncado=True, n_gold=1, firma="0" * 64))
    assert d["estado"] == "parcial" and "--estado" in d["motivo"] and "2 000 versiones" in d["motivo"], d
    d = asm.estado_dataset(str(store), dict(res, transitorias=1))
    assert d["estado"] == "parcial" and "transitori" in d["motivo"], d


def test_t10fix2_m10_estado_dataset_tiene_margen_propio_tras_el_recuento(tmp_path):
    """M10: `estado_dataset` tiene margen propio (`hasta + MARGEN_ESTADO_S`): aunque el recuento haya
    agotado su plazo, lee la marca y lista `exports/`."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    res = rec.resumen_store(str(store), raiz)
    assert 0 < asm.MARGEN_ESTADO_S <= 0.3
    d = asm.estado_dataset(str(store), res, hasta=rec._crono())
    assert d["estado"] == "al_dia" and d["exports"] == 1, d


def _bloquear_exclusivo(ruta):
    """Abre `ruta` con `CreateFileW` y `dwShareMode = 0` (Windows): cualquier otro `open` falla con
    `PermissionError` mientras el handle vive. None fuera de Windows."""
    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                                wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    h = k32.CreateFileW(str(ruta), 0x80000000, 0, None, 3, 0x80, None)
    assert h not in (None, wintypes.HANDLE(-1).value), ctypes.get_last_error()
    return lambda: k32.CloseHandle(h)


def test_t10fix2_170_la_lectura_de_la_marca_respeta_el_plazo(tmp_path, monkeypatch):
    """#170: la marca con un bloqueo exclusivo (antivirus, backup): sus reintentos se acotan por el
    plazo de `/doctor` (+ el margen propio de M10) y la frescura sale «no verificado (PARCIAL)»
    (antes: 40 x 25 ms = 1 s con un plazo de 50 ms). En Windows el bloqueo es REAL (`CreateFileW`,
    share 0); en POSIX, donde no hay bloqueo obligatorio, se simula con `PermissionError`."""
    monkeypatch.setattr(rec, "_PERMISOS_PERMANENTES", False)   # N6 (fix3): simula el bloqueo TRANSITORIO de Windows
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    res = rec.resumen_store(str(store), raiz)
    ruta = store / "exports" / asm.MARCA
    soltar = _bloquear_exclusivo(ruta)
    if soltar is None:
        real = rec._abrir_lectura

        def bloqueado(r):
            if os.path.basename(str(r)) == asm.MARCA:
                raise PermissionError(13, "bloqueado")
            return real(r)
        monkeypatch.setattr(rec, "_abrir_lectura", bloqueado)
        soltar = lambda: monkeypatch.setattr(rec, "_abrir_lectura", real)          # noqa: E731
    try:
        t0 = time.monotonic()
        hasta = rec._crono() + 0.05
        d = asm.estado_dataset(str(store), res, hasta=hasta)
        dura = time.monotonic() - t0
    finally:
        soltar()
    assert d["estado"] == "parcial", d
    assert dura <= 0.05 + asm.MARGEN_ESTADO_S + 0.3, dura
    d = asm.estado_dataset(str(store), res, hasta=rec._crono() + 0.05)
    assert d["estado"] == "al_dia", d


def test_t10fix2_176_frescura_verificable_aunque_el_manifiesto_pase_del_tope(tmp_path):
    """#176: a ~13 700 Gold el `manifest.json` pasa de `TOPE_FICHERO` y la frescura quedaba SIEMPRE
    `no_verificable`: con D-f4 no se lee (solo se comprueba que sea un fichero regular) y
    `--estado` la verifica sin tope."""
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz, escribir=True)
    man = os.path.join(r["ruta"], asm.MANIFEST)
    with open(man, "r+b") as f:
        f.truncate(asm.TOPE_FICHERO + 1)                            # disperso: el tamaño de ~13 700 Gold
    assert _estado(store, raiz)["estado"] == "al_dia"
    assert asm.main(["--estado", "--project-root", raiz]) == 0


def test_t10fix2_176_estado_cli_exit_y_misma_salida_que_doctor(tmp_path, capsys):
    """#176 / F4: `dataset-assembler.py --estado` (solo lectura, sin plazo, sin `exports/.lock`): la
    MISMA salida que `/doctor` (texto y `--json`); exit 0 `al_dia`/`sin_gold` · 1
    `desactualizado`/`sin_export` · 2 `no_verificable`/`parcial` o config que no vale."""
    raiz, cfg, store = _store_basico(tmp_path)
    assert asm.main(["--estado", "--project-root", raiz]) == 1                 # sin_export
    assert "dataset: desactualizado" in capsys.readouterr().out
    _ensamblar(cfg, raiz, escribir=True)
    assert asm.main(["--estado", "--project-root", raiz]) == 0
    texto = capsys.readouterr().out.strip()
    esperado = asm.texto_estado(rec.resumen_store(str(store), raiz, plazo_s=None),
                                asm.estado_dataset(str(store), rec.resumen_store(str(store), raiz, plazo_s=None)))
    assert texto == esperado and "dataset: al dia" in texto and "PARCIAL" not in texto
    assert asm.main(["--estado", "--json", "--project-root", raiz]) == 0
    j = json.loads(capsys.readouterr().out)
    assert j["dataset"]["estado"] == "al_dia" and j["recuento"]["n_gold"] == 3 and j["texto"] == esperado
    assert "gold" not in j["recuento"] and "hasta" not in j["recuento"]
    _grabar(cfg, raiz, family="c", variant="x", request="escalera de caracol con barandilla de hierro forjado")
    assert asm.main(["--estado", "--project-root", raiz]) == 1
    (store / "exports" / asm.MARCA).write_text("{}", encoding="utf-8")
    assert asm.main(["--estado", "--project-root", raiz]) == 2
    capsys.readouterr()
    (tmp_path / "sin-config").mkdir()
    assert asm.main(["--estado", "--project-root", str(tmp_path / "sin-config")]) == 2


def test_t10fix2_176_estado_no_toma_el_bloqueo_ni_escribe(tmp_path):
    """F4: `--estado` es de solo lectura y no espera a `exports/.lock` (otro ensamblador en marcha)."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    antes = sorted((p, os.path.getsize(os.path.join(b, p))) for b, _d, fs in os.walk(str(store)) for p in fs
                   if p != asm.BLOQUEO_EXPORTS)
    h, soltar = _con_lock_tomado(store, 30)
    try:
        t0 = time.monotonic()
        assert asm.main(["--estado", "--project-root", raiz]) == 0
        assert time.monotonic() - t0 < 10
    finally:
        soltar.set()
        h.join(10)
    despues = sorted((p, os.path.getsize(os.path.join(b, p))) for b, _d, fs in os.walk(str(store)) for p in fs
                     if p != asm.BLOQUEO_EXPORTS)
    assert despues == antes


def test_t10fix2_m13_seis_ensambladores_dejan_una_marca_coherente(tmp_path):
    """M13: 6 ensambladores reales a la vez -> una sola marca, coherente con un export EXISTENTE y con
    la firma del store (la de la pasada 1 del que la escribio): `al_dia`."""
    raiz, cfg, store = _store_basico(tmp_path)
    procs = [_ensamblador_proceso(raiz) for _ in range(6)]
    salidas = [p.communicate(timeout=120) for p in procs]
    assert [p.returncode for p in procs] == [0] * 6, salidas
    m = _marca(store)
    assert os.path.isfile(str(store / "exports" / m["directorio"] / asm.MANIFEST))
    assert _exports(store) == [m["directorio"]]
    assert m["firma"] == rec.resumen_store(str(store), raiz)["firma"]
    assert _estado(store, raiz)["estado"] == "al_dia"
    assert not [n for n in os.listdir(str(store / "exports")) if n.startswith(rec.PREFIJO_TEMPORAL)]


def test_t10fix2_m12_el_limite_de_sistemas_de_ficheros_locales_esta_declarado():
    """M12: una sola llamada del SO que se bloquea (SMB colgado, placeholder de OneDrive) no la acota
    ninguna comprobacion ENTRE llamadas: el tope de `/doctor` vale para sistemas de ficheros locales.
    Este test fija que el limite esta declarado en la doc de `/doctor` y en `references/dataset.md`."""
    raiz_repo = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
    for rel in (os.path.join("commands", "doctor.md"),
                os.path.join("skills", "training-data-services", "references", "dataset.md")):
        with open(os.path.join(raiz_repo, rel), encoding="utf-8") as f:
            texto = f.read()
        assert "sistemas de ficheros locales" in texto, rel


# ------------------------------------------------------------------ T-10 fix2 #178: CLI y ramas EN PROCESO

def test_t10fix2_178_cli_en_proceso_exit_y_mensajes(tmp_path, capsys, monkeypatch):
    """#178: `main([...])` en proceso: ok, `--dry-run`, sin benchmark (1), fecha invalida (2), config
    rota (2), otro ensamblador con el bloqueo (3), `Rechazo` con errores (1), E/S (2) y sin `redact.py` (2)."""
    raiz, cfg, store = _store_basico(tmp_path)
    assert asm.main(["--project-root", raiz, "--benchmark", "bench", "--fecha", FECHA]) == 0
    assert " escrito: " in capsys.readouterr().out
    assert asm.main(["--project-root", raiz, "--benchmark", "bench", "--fecha", FECHA]) == 0
    assert "ya existe" in capsys.readouterr().out
    assert asm.main(["--project-root", raiz, "--benchmark", "bench", "--fecha", FECHA, "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["export_id"]
    assert asm.main(["--project-root", raiz]) == 1 and "benchmark" in capsys.readouterr().err
    assert asm.main(["--project-root", raiz, "--benchmark", "bench", "--fecha", "2026-13-01"]) == 2
    roto = tmp_path / "roto.json"
    roto.write_text("{", encoding="utf-8")
    assert asm.main(["--config", str(roto), "--project-root", raiz, "--benchmark", "bench"]) == 2
    malo = tmp_path / "proj" / ".claude" / "knowledge-services" / "training.json"
    bueno = malo.read_text(encoding="utf-8")
    malo.write_text(json.dumps({"version": 1, "enabled": "si"}), encoding="utf-8")
    assert asm.main(["--project-root", raiz, "--benchmark", "bench"]) == 1
    assert "enabled" in capsys.readouterr().err
    malo.write_text(bueno, encoding="utf-8")
    h, soltar = _con_lock_tomado(store, 30)
    try:
        _grabar(cfg, raiz, family="c", variant="x", request="escalera de caracol con barandilla de hierro forjado")
        assert asm.main(["--project-root", raiz, "--benchmark", "bench", "--espera-bloqueo", "0.2"]) == 3
    finally:
        soltar.set()
        h.join(10)

    def falla(exc):
        def _f(*a, **k):
            raise exc
        return _f
    monkeypatch.setattr(asm, "ensamblar", falla(OSError(5, "disco")))
    assert asm.main(["--project-root", raiz, "--benchmark", "bench"]) == 2
    monkeypatch.setattr(asm, "ensamblar", falla(rec.RedaccionNoDisponible("sin redact")))
    assert asm.main(["--project-root", raiz, "--benchmark", "bench"]) == 2
    capsys.readouterr()


def test_t10fix2_178_la_marca_avisa_en_la_salida_del_cli(tmp_path, capsys):
    raiz, cfg, store = _store_basico(tmp_path)
    (store / "exports").mkdir(parents=True)
    (store / "exports" / asm.MARCA).write_text("{}", encoding="utf-8")
    assert asm.main(["--project-root", raiz, "--benchmark", "bench", "--fecha", FECHA]) == 0
    assert "aviso: " in capsys.readouterr().err


def test_t10fix2_178_esquema_y_lectura_de_la_marca_ramas():
    """#178: cada motivo de `_motivo_marca`, `_bytes_marca` con parametros que no caben y
    `_texto_parametros` sin parametros."""
    base = {"version": 1, "export_id": "20260101-0123456789ab", "directorio": "20260101-0123456789ab",
            "firma": "a" * 64, "gold": 1, "creado": "2026-01-01T00:00:00Z", "parametros": {},
            "omitidos": 0, "omitidos_muestra": []}                            # D-f5 O2 (fix3)
    assert asm._motivo_marca(base) is None
    for cambio, motivo in (({"version": True}, "version"), ({"export_id": "x"}, "export_id"),
                           ({"directorio": "20260101-ffffffffffff"}, "directorio"), ({"firma": "A" * 64}, "firma"),
                           ({"gold": -1}, "Gold"), ({"creado": 5}, "creado"), ({"parametros": []}, "parametros")):
        assert motivo in asm._motivo_marca(dict(base, **cambio)), cambio
    assert "esquema" in asm._motivo_marca(dict(base, extra=1))
    grande = dict(base, parametros={"benchmark": [f"familia-{i:04d}" for i in range(400)]})
    datos = asm._bytes_marca(grande)
    assert len(datos) <= asm.TOPE_MARCA and json.loads(datos)["parametros"]["benchmark"] == "400 familias"
    enorme = dict(base, parametros={"benchmark": ["f"], "otro": "x" * 5000})
    assert json.loads(asm._bytes_marca(enorme))["parametros"] == {}
    assert asm._texto_parametros(None) == "sin parametros registrados"
    assert "benchmark=a,b" in asm._texto_parametros({"benchmark": ["a", "b"], "conservar_duplicados": True})


def test_t10fix2_178_leer_marca_ramas(tmp_path, monkeypatch):
    """#178: `_leer_marca` con la marca que no se puede examinar, que es un directorio, que no es del
    descriptor esperado y que no es JSON."""
    ex = tmp_path / "exports"
    ex.mkdir()
    (ex / asm.MARCA).mkdir()
    assert "no es un fichero regular" in asm._leer_marca(str(ex))[1]
    os.rmdir(str(ex / asm.MARCA))
    (ex / asm.MARCA).write_text("{roto", encoding="utf-8")
    assert "no se puede leer" in asm._leer_marca(str(ex))[1]
    real = rec._leer_json_reintentando

    def ajeno(*a, **k):
        raise rec._FicheroNoPropio("sustituido")
    monkeypatch.setattr(rec, "_leer_json_reintentando", ajeno)
    assert "sustituido" in asm._leer_marca(str(ex))[1]
    monkeypatch.setattr(rec, "_leer_json_reintentando", real)

    def sin_permiso(x):
        raise PermissionError(13, "no")
    monkeypatch.setattr(rec, "_stat_sin_seguir", sin_permiso)
    assert "no se puede examinar" in asm._leer_marca(str(ex))[1]


def test_t10fix2_178_estado_dataset_ramas_de_exports(tmp_path, monkeypatch):
    """#178: `exports/` que no se puede listar, el export de la marca que ya no esta completo, un
    corte a mitad del listado y el texto con exports incompletos/en curso/otros."""
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz, escribir=True)
    res = rec.resumen_store(str(store), raiz)
    os.remove(os.path.join(r["ruta"], asm.MANIFEST))
    (store / "exports" / "20250101-bbbbbbbbbbbb").mkdir()
    d = asm.estado_dataset(str(store), res)
    assert d["estado"] == "sin_export", d
    otro = _ensamblar(cfg, raiz, escribir=True, umbral=0.5)
    shutil.rmtree(otro["ruta"])
    (store / "exports" / "20260101-000000000000").mkdir()
    (store / "exports" / "20260101-000000000000" / asm.MANIFEST).write_text("{}", encoding="utf-8")
    d = asm.estado_dataset(str(store), res)
    assert d["estado"] == "no_verificable" and "ya no esta completo" in d["motivo"], d
    for i in range(70):
        (store / "exports" / f"x{i:03d}").write_text("x", encoding="utf-8")
    reloj = iter(range(0, 10_000))
    monkeypatch.setattr(rec, "_crono", lambda: next(reloj) * 0.1)
    d = asm.estado_dataset(str(store), res, hasta=0.0)
    assert d["estado"] == "parcial", d
    monkeypatch.undo()
    texto = asm.texto_estado(dict(res, grandes=1, cortadas=1, otros_avisos=1, en_curso=1, truncado=True,
                                  listado_parcial=True, casos_vistos=1, casos_total=2, plazo_s=2.0),
                             dict(asm.estado_dataset(str(store), res), incompletos=1, en_curso=1, otros=1))
    for trozo in ("demasiado grandes 1", "cortadas por el tope 1", "otros avisos 1", "en curso 1", "al menos 2",
                  "export(s) incompleto(s)", "export(s) en curso", "que no son un export"):
        assert trozo in texto, (trozo, texto)
    real = os.scandir

    def roto(ruta="."):
        if os.path.basename(str(ruta)) == "exports":
            raise PermissionError(13, "no")
        return real(ruta)
    monkeypatch.setattr(os, "scandir", roto)
    assert asm.estado_dataset(str(store), res)["estado"] == "no_verificable"


# ------------------------------------------------------------------ T-10 fix3 (#180-#186, D-f5 con N1-N9)

LITERALES_180 = ("\x1b]0;pwn\x07‮", "\x1b[2J‮FALSO\n linea")
PROHIBIDOS_180 = ("\x1b", "‮", "\u009b", " ", "\n")
PARAMETROS_OK = {"benchmark": ["bench"], "umbral": 0.8, "ventana": 3, "fraccion_boilerplate": 0.5,
                 "n_min_boilerplate": 5, "presupuesto": 10_000_000, "tope_fichero": 16 * 1024 * 1024,
                 "conservar_duplicados": False}
MARCA_OK = {"version": 1, "export_id": "20260101-0123456789ab", "directorio": "20260101-0123456789ab",
            "firma": "a" * 64, "gold": 1, "creado": "2026-01-01T00:00:00Z", "parametros": dict(PARAMETROS_OK),
            "omitidos": 0, "omitidos_muestra": []}
OMISION_OK = {"ref": "geo-a.x@v001", "clase": "permanente", "causa": "ausente"}


def _sin_prohibidos(texto):
    return not any(c in texto for c in PROHIBIDOS_180)


def _escribir_marca_a_mano(store, marca):
    (store / "exports" / asm.MARCA).write_text(json.dumps(marca, ensure_ascii=False), encoding="utf-8")


def test_t10fix3_180_n1_parametros_con_el_esquema_exacto_del_ensamblador():
    """#180/N1: `parametros` de la marca = EXACTAMENTE lo que escribe el ensamblador: `umbral` y
    `fraccion_boilerplate` numeros finitos en (0, 1]; `ventana`, `n_min_boilerplate`, `presupuesto` y
    `tope_fichero` enteros >= 1 (un bool no vale); `conservar_duplicados` bool; `benchmark` lista de
    cadenas de <= 256 caracteres, `"<n> familias"` o ausente; tambien `{}`. Cualquier otra cosa (clave
    desconocida incluida) -> marca invalida."""
    assert asm._motivo_marca(MARCA_OK) is None
    buenos = [{}, dict(PARAMETROS_OK, benchmark="400 familias"),
              {k: v for k, v in PARAMETROS_OK.items() if k != "benchmark"}, dict(PARAMETROS_OK, umbral=1),
              dict(PARAMETROS_OK, benchmark=["x" * 256, "ñandú"]), dict(PARAMETROS_OK, conservar_duplicados=True)]
    for p in buenos:
        assert asm._motivo_marca(dict(MARCA_OK, parametros=p)) is None, p
    malos = [dict(PARAMETROS_OK, umbral=LITERALES_180[0]), dict(PARAMETROS_OK, umbral=LITERALES_180[1]),
             dict(PARAMETROS_OK, umbral=0), dict(PARAMETROS_OK, umbral=1.5), dict(PARAMETROS_OK, umbral=float("nan")),
             dict(PARAMETROS_OK, umbral=float("inf")), dict(PARAMETROS_OK, umbral=True), dict(PARAMETROS_OK, umbral="0.8"),
             dict(PARAMETROS_OK, fraccion_boilerplate=0.0), dict(PARAMETROS_OK, ventana=0),
             dict(PARAMETROS_OK, ventana=True), dict(PARAMETROS_OK, ventana=1.5), dict(PARAMETROS_OK, presupuesto="1"),
             dict(PARAMETROS_OK, tope_fichero=0), dict(PARAMETROS_OK, n_min_boilerplate=LITERALES_180[0]),
             dict(PARAMETROS_OK, conservar_duplicados=1), dict(PARAMETROS_OK, benchmark=[1]),
             dict(PARAMETROS_OK, benchmark=["x" * 257]), dict(PARAMETROS_OK, benchmark="tres familias"),
             dict(PARAMETROS_OK, benchmark="3 familias\n"), dict(PARAMETROS_OK, benchmark=LITERALES_180[1]),
             dict(PARAMETROS_OK, benchmark={"a": 1}), dict(PARAMETROS_OK, extra=1),
             {k: v for k, v in PARAMETROS_OK.items() if k != "n_min_boilerplate"}, []]
    for p in malos:
        assert asm._motivo_marca(dict(MARCA_OK, parametros=p)) is not None, p


def test_t10fix3_180_n1_toda_marca_que_escribe_el_ensamblador_pasa_su_lector(tmp_path):
    """#180/N1 (I1): ida y vuelta: toda marca que produce el escritor —la de un ensamblado real y la de
    cada fallback de `_bytes_marca` (muestra recortada, `benchmark` resumido, `parametros` = {})— pasa
    `_motivo_marca` y cabe en `TOPE_MARCA`."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    assert asm._motivo_marca(_marca(store)) is None
    largas = [{"ref": "g" * 200 + f"@v{i:03d}", "clase": "transitorio", "causa": "sin permisos o bloqueado"}
              for i in range(10)]
    variantes = [dict(MARCA_OK), dict(MARCA_OK, omitidos=40, omitidos_muestra=largas),
                 dict(MARCA_OK, parametros=dict(PARAMETROS_OK, benchmark=["f" * 256] * 60)),
                 dict(MARCA_OK, omitidos=40, omitidos_muestra=largas,
                      parametros=dict(PARAMETROS_OK, benchmark=["f" * 256] * 60))]
    for m in variantes:
        datos = asm._bytes_marca(m)
        assert len(datos) <= asm.TOPE_MARCA, len(datos)
        leida = json.loads(datos)
        assert asm._motivo_marca(leida) is None, (asm._motivo_marca(leida), leida)
        assert leida["omitidos"] == m["omitidos"]


def test_t10fix3_180_marca_forjada_con_escapes_no_llega_cruda_a_estado(tmp_path, capsys):
    """#180 (CWE-150): una marca con firma valida y `parametros` forjados (`umbral` con OSC que cambia el
    titulo del terminal, borrado de pantalla, bidi y un salto de linea) es INVALIDA (`no_verificable`):
    ni el texto de `/doctor` (`texto_estado`) ni `--estado` ni `--estado --json` sacan ESC, U+202E,
    U+009B, U+2028 ni `\\n`."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    buena = _marca(store)
    for lit in LITERALES_180:
        _escribir_marca_a_mano(store, dict(buena, parametros=dict(buena["parametros"], umbral=lit)))
        res = _vigentes(store, raiz)
        d = asm.estado_dataset(str(store), res)
        assert d["estado"] == "no_verificable", d
        assert _sin_prohibidos(asm.texto_estado(res, d))
        capsys.readouterr()
        assert asm.main(["--estado", "--project-root", raiz]) == 2
        salida = capsys.readouterr()
        assert _sin_prohibidos(salida.out.rstrip("\n")) and _sin_prohibidos(salida.err.rstrip("\n")), salida
        assert asm.main(["--estado", "--json", "--project-root", raiz]) == 2
        datos = json.loads(capsys.readouterr().out)
        assert _sin_prohibidos(datos["texto"]) and datos["dataset"]["parametros"] is None, datos["dataset"]


def test_t10fix3_180_texto_parametros_escapa_todo_valor():
    """#180 (b, defensa en profundidad): `_texto_parametros` pasa TODO valor por `rec._texto_ruta`,
    aunque llegara uno que no pasara el esquema."""
    for lit in LITERALES_180:
        p = {"benchmark": [lit], "umbral": lit, "ventana": lit, "fraccion_boilerplate": lit,
             "conservar_duplicados": lit}
        assert _sin_prohibidos(asm._texto_parametros(p)), asm._texto_parametros(p)
        assert _sin_prohibidos(asm._texto_parametros(dict(p, benchmark=lit)))


def test_t10fix3_181_otro_id_prefix_excluido_en_los_dos_lados_y_fuera_del_export(tmp_path):
    """#181/N2: una version con OTRO `id_prefix` (el de training.json cambio, o plantada) se omite en
    `_estado_de_cases` en los DOS lados: ni `resumen_store` ni la pasada 1 la cuentan, no aparece en el
    manifiesto ni en el export. fix4 (#190): la frescura ya no sale `al_dia` sino `con_omisiones` con la
    causa «1 version con otro `id_prefix`…» PRIMERO (exit 1); sin ella, `al_dia`."""
    raiz, cfg, store = _store_basico(tmp_path)
    otra = dict(cfg, id_prefix="otro")
    r = rec.grabar(_caso(family="c", variant="x", request="pieza de otro prefijo con tres agujeros"), otra, raiz)
    rec.cambiar_estado(r["case_id"], 1, "approved", otra, raiz, approved_by_human=True)
    assert r["case_id"] == "otro-c.x"
    e = _ensamblar(cfg, raiz, escribir=True)
    man = _manifest(e)
    assert not any("otro-c.x" in c["ref"] or c["family"] == "c" for c in man["casos"]), man["casos"]
    for f in asm.JSONL:
        assert "otro-c.x" not in open(os.path.join(e["ruta"], f), encoding="utf-8").read()
    assert any("cases/c.x" in a and "id_prefix" in a and "otro-c.x" not in a for a in e["avisos_store"]), e["avisos_store"]
    res = rec.resumen_store(str(store), raiz, id_prefix="geo")
    assert ("otro-c.x", 1) not in res["gold"] and res["n_gold"] == 3
    d = asm.estado_dataset(str(store), res)
    assert _marca(store)["gold"] == 3 and d["estado"] == "con_omisiones", d
    assert d["motivo"].startswith(asm.causa_otro_prefijo(1)) and "otro-c.x" not in d["motivo"], d
    assert asm.main(["--estado", "--project-root", raiz]) == 1
    shutil.rmtree(str(store / "cases" / "c.x"))
    assert asm.main(["--estado", "--project-root", raiz]) == 0


def test_t10fix3_182_b1_omision_permanente_con_omisiones_hasta_reensamblar(tmp_path):
    """#182 cara 1 / D-f5 (B1 literal): se renombra `trajectory.jsonl` de un Gold -> ensamblar (el
    Gold queda FUERA del dataset pero dentro de la firma, O1) -> `con_omisiones` -> se restaura ->
    SIGUE `con_omisiones` (nunca un `al_dia` que oculte un Gold fuera del dataset) -> reensamblar ->
    `al_dia`."""
    raiz, cfg, store = _store_basico(tmp_path)
    tr = store / "cases" / "a.x" / "v002" / "trajectory.jsonl"
    aparte = tr.with_name("trajectory.jsonl.aparte")
    tr.rename(aparte)
    r = _ensamblar(cfg, raiz, escribir=True)
    assert any(c["ref"] == "geo-a.x@v002" and c["particion"] is None for c in _manifest(r)["casos"])
    m = _marca(store)
    assert m["omitidos"] == 1 and m["omitidos_muestra"] == [dict(OMISION_OK, ref="geo-a.x@v002")], m
    assert m["firma"] == _vigentes(store, raiz)["firma"]                  # O1: el omitido sigue en la firma
    d = _estado(store, raiz)
    assert d["estado"] == "con_omisiones", d
    for trozo in ("1 Gold omitido", "geo-a.x@v002", "ausente", "reensambla", "set-status", "rejected"):
        assert trozo in d["motivo"], (trozo, d["motivo"])
    aparte.rename(tr)
    assert _estado(store, raiz)["estado"] == "con_omisiones"
    r2 = _ensamblar(cfg, raiz, escribir=True)
    assert r2["existente"] is False and _marca(store)["omitidos"] == 0
    assert _estado(store, raiz)["estado"] == "al_dia"


def _sin_permiso_en(monkeypatch, ruta, errno_=13):
    real = rec._abrir_lectura
    objetivo = os.path.normcase(str(ruta))

    def bloqueado(r):
        if os.path.normcase(str(r)) == objetivo:
            raise PermissionError(errno_, "sin permiso")
        return real(r)
    monkeypatch.setattr(rec, "_abrir_lectura", bloqueado)
    monkeypatch.setattr(rec, "ESPERA_REINTENTO_S", 0.0)
    return lambda: monkeypatch.setattr(rec, "_abrir_lectura", real)


def test_t10fix3_182_b2_sin_permisos_con_omisiones_y_reensamblar_limpia(tmp_path, monkeypatch):
    """#182 cara 2 / D-f5 (B2 literal): `chmod 000` en `request.json` de un Gold (POSIX sin root; como
    root o en Windows, `PermissionError` simulado) -> `con_omisiones` con su clase y su causa (N6: en
    POSIX `permanente`/«sin permisos», en Windows `transitorio`/«sin permisos o bloqueado») -> se
    devuelve el permiso -> reensamblar -> `al_dia` (antes: `desactualizado` que reensamblar NUNCA
    limpiaba)."""
    raiz, cfg, store = _store_basico(tmp_path)
    req = store / "cases" / "a.x" / "v002" / "request.json"
    real_chmod = os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() != 0
    if real_chmod:
        os.chmod(str(req), 0)
        devolver = lambda: os.chmod(str(req), 0o644)                     # noqa: E731
    else:
        devolver = _sin_permiso_en(monkeypatch, req)
    esperado = (("permanente", "sin permisos") if rec._PERMISOS_PERMANENTES
                else ("transitorio", "sin permisos o bloqueado"))
    try:
        _ensamblar(cfg, raiz, escribir=True)
    finally:
        devolver()
    m = _marca(store)
    assert m["omitidos"] == 1 and m["omitidos_muestra"] == [
        {"ref": "geo-a.x@v002", "clase": esperado[0], "causa": esperado[1]}], m
    d = _estado(store, raiz)
    assert d["estado"] == "con_omisiones" and esperado[1] in d["motivo"], d
    if esperado[0] == "permanente":
        assert "revisa los permisos" in d["motivo"], d
    r2 = _ensamblar(cfg, raiz, escribir=True)
    assert r2["existente"] is False and _estado(store, raiz)["estado"] == "al_dia"


def test_t10fix3_182_n6_eacces_en_posix_es_permanente_en_el_ensamblador(tmp_path, monkeypatch):
    """N6 (decidido), en cualquier plataforma: con `_PERMISOS_PERMANENTES` (POSIX) un `EACCES` es una
    omision PERMANENTE, causa «sin permisos», con el remedio «revisa los permisos y reensambla»."""
    import errno as _errno
    monkeypatch.setattr(rec, "_PERMISOS_PERMANENTES", True)
    raiz, cfg, store = _store_basico(tmp_path)
    devolver = _sin_permiso_en(monkeypatch, store / "cases" / "a.x" / "v002" / "request.json", _errno.EACCES)
    _ensamblar(cfg, raiz, escribir=True)
    devolver()
    assert _marca(store)["omitidos_muestra"] == [{"ref": "geo-a.x@v002", "clase": "permanente",
                                                  "causa": "sin permisos"}]
    d = _estado(store, raiz)
    assert d["estado"] == "con_omisiones" and "revisa los permisos" in d["motivo"], d


def test_t10fix3_182_muestra_de_10_con_el_numero_real_de_omisiones(tmp_path):
    """D-f5: con 12 omisiones, la muestra guarda 10 y `omitidos` el numero real."""
    raiz, cfg, store = _proyecto(tmp_path)
    for i in range(12):
        _grabar(cfg, raiz, family=f"f{i:02d}", variant="x", request=f"pieza numero {i} con {i + 3} caras distintas")
    _grabar(cfg, raiz, family="bench", variant="x", request="engranaje de doce dientes con eje de acero")
    for i in range(12):
        (store / "cases" / f"f{i:02d}.x" / "v001" / "trajectory.jsonl").write_text("{roto\n", encoding="utf-8")
    _ensamblar(cfg, raiz, escribir=True)
    m = _marca(store)
    assert m["omitidos"] == 12 and len(m["omitidos_muestra"]) == 10, m
    assert {(o["clase"], o["causa"]) for o in m["omitidos_muestra"]} == {("permanente", "ilegible")}
    d = _estado(store, raiz)
    assert d["estado"] == "con_omisiones" and "12 Gold omitidos" in d["motivo"], d


def test_t10fix3_182_esquema_de_las_omisiones_de_la_marca():
    """D-f5 O2 + N3: `omitidos` entero >= 0 (un bool no vale) y `omitidos_muestra` lista de <= 10
    (y <= `omitidos`) objetos `{ref, clase, causa}`: `ref` CRUDA que casa `PATRON_REFERENCIA` con un
    `case_id` <= `CASE_ID_MAX`, `clase` transitorio|permanente y `causa` normalizada. Si no, la marca es
    invalida."""
    for ok in (dict(MARCA_OK, omitidos=1, omitidos_muestra=[OMISION_OK]), dict(MARCA_OK, omitidos=5),
               dict(MARCA_OK, omitidos=11, omitidos_muestra=[OMISION_OK] * 10),
               dict(MARCA_OK, omitidos=1, omitidos_muestra=[dict(OMISION_OK, ref="p-ñandú.x@v001")])):
        assert asm._motivo_marca(ok) is None, ok
    malos = [{"omitidos": -1}, {"omitidos": 1.5}, {"omitidos": True}, {"omitidos": "1"},
             {"omitidos": 11, "omitidos_muestra": [OMISION_OK] * 11},
             {"omitidos": 0, "omitidos_muestra": [OMISION_OK]},
             {"omitidos": 1, "omitidos_muestra": ["geo-a.x@v001"]},
             {"omitidos": 1, "omitidos_muestra": [dict(OMISION_OK, ref="sin-arroba")]},
             {"omitidos": 1, "omitidos_muestra": [dict(OMISION_OK, ref="'geo-\\xf1.x@v001'")]},
             {"omitidos": 1, "omitidos_muestra": [dict(OMISION_OK, ref="g" * 201 + "@v001")]},
             {"omitidos": 1, "omitidos_muestra": [dict(OMISION_OK, clase="otra")]},
             {"omitidos": 1, "omitidos_muestra": [dict(OMISION_OK, causa="x")]},
             {"omitidos": 1, "omitidos_muestra": [dict(OMISION_OK, extra=1)]},
             {"omitidos_muestra": "x"}]
    for cambio in malos:
        assert asm._motivo_marca(dict(MARCA_OK, **cambio)) is not None, cambio
    assert "esquema" in asm._motivo_marca({k: v for k, v in MARCA_OK.items() if k != "omitidos"})


def test_t10fix3_182_n3_muestra_no_ascii_y_larga_cabe_en_4_kib_y_la_lee_su_lector(tmp_path):
    """N3 (I2): con un `family_pattern` que admite no ASCII, la muestra guarda la referencia CRUDA (casa
    `PATRON_REFERENCIA`; escapada no casaria) y se escapa solo al mostrarla; `_bytes_marca` recorta
    primero la muestra hasta caber en 4 KiB (11 omisiones con `case_id` de 200 caracteres no ASCII), y el
    lector la acepta."""
    raiz, cfg, store = _proyecto(tmp_path, ids={"family_pattern": r"^\w+$", "variant_pattern": r"^\w+$"})
    for i in range(3):
        _grabar(cfg, raiz, family=f"ñandú{i}", variant="x", request=f"pieza no ascii numero {i} con ojales")
    _grabar(cfg, raiz, family="bench", variant="x", request="engranaje de doce dientes con eje de acero")
    for i in range(3):
        (store / "cases" / f"ñandú{i}.x" / "v001" / "trajectory.jsonl").write_text("{roto\n", encoding="utf-8")
    _ensamblar(cfg, raiz, escribir=True)
    m = _marca(store)
    assert m["omitidos"] == 3 and m["omitidos_muestra"][0]["ref"] == "geo-ñandú0.x@v001", m
    d = _estado(store, raiz)
    assert d["estado"] == "con_omisiones" and "ñ" not in d["motivo"] and "\\xf1" in d["motivo"], d
    largas = [{"ref": "ñ" * 200 + f"@v{i:03d}", "clase": "permanente", "causa": "ilegible"} for i in range(11)]
    datos = asm._bytes_marca(dict(MARCA_OK, omitidos=11, omitidos_muestra=largas[:10]))
    leida = json.loads(datos)
    assert len(datos) <= asm.TOPE_MARCA and asm._motivo_marca(leida) is None, len(datos)
    assert leida["omitidos"] == 11 and 0 < len(leida["omitidos_muestra"]) < 10
    assert leida["parametros"] == PARAMETROS_OK                          # recorta la muestra ANTES que nada


def test_t10fix3_182_n3_escribir_marca_no_publica_lo_que_su_lector_rechazaria(tmp_path, monkeypatch):
    """N3: `_escribir_marca` valida con `_motivo_marca` y con el tope los bytes EXACTOS que va a publicar:
    si no pasan, no escribe (la marca anterior queda intacta, sin temporal) y avisa."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    ruta = store / "exports" / asm.MARCA
    antes = ruta.read_bytes()
    for malos in (b'{"version": 1}\n', b"{" + b" " * (asm.TOPE_MARCA + 10) + b"}\n", b"no es json\n"):
        monkeypatch.setattr(asm, "_bytes_marca", lambda m, _b=malos: _b)
        r = _ensamblar(cfg, raiz, escribir=True)
        assert r["existente"] is True and r["aviso_marca"] and "no se publica" in r["aviso_marca"], r["aviso_marca"]
        assert ruta.read_bytes() == antes
        assert not [n for n in os.listdir(str(store / "exports")) if n.startswith(rec.PREFIJO_TEMPORAL)]


def test_t10fix3_182_o1_la_firma_ya_no_lleva_transitoria(tmp_path, monkeypatch):
    """O1: todo Gold vigente entra en la firma con su `content_hash` saneado, lo haya incluido
    `leer_caso` o no; `"!transitoria"` se retira (la firma describe solo el conjunto de Gold)."""
    assert not hasattr(rec, "TRANSITORIA")
    raiz, cfg, store = _store_basico(tmp_path)
    devolver = _sin_permiso_en(monkeypatch, store / "cases" / "a.x" / "v001" / "request.json")
    monkeypatch.setattr(rec, "_PERMISOS_PERMANENTES", False)
    _ensamblar(cfg, raiz, escribir=True)
    devolver()
    assert _marca(store)["firma"] == _vigentes(store, raiz)["firma"]


def test_t10fix3_183_todos_los_gold_rechazados_con_su_export_es_desactualizado(tmp_path, capsys):
    """#183/N7: con exports y TODOS los Gold rechazados despues, la marca valida con `gold > 0` y su
    export completo -> `desactualizado` (exit 1) con el remedio de archivarlo; tras archivar ese export
    (o sin marca) -> `sin_gold`, como hoy."""
    raiz, cfg, store = _store_basico(tmp_path)
    r = _ensamblar(cfg, raiz, escribir=True)
    for cid, v in (("geo-a.x", 1), ("geo-a.x", 2), ("geo-bench.x", 1)):
        rec.cambiar_estado(cid, v, "rejected", cfg, raiz)
    d = _estado(store, raiz)
    assert d["estado"] == "desactualizado", d
    for trozo in ("0 Gold vigentes frente a 3", os.path.basename(r["ruta"]), "no se puede reensamblar", "archivalo"):
        assert trozo in d["motivo"], (trozo, d["motivo"])
    assert asm.main(["--estado", "--project-root", raiz]) == 1
    capsys.readouterr()
    shutil.move(r["ruta"], str(tmp_path / "archivado"))
    assert _estado(store, raiz)["estado"] == "sin_gold"
    os.remove(str(store / "exports" / asm.MARCA))
    assert _estado(store, raiz)["estado"] == "sin_gold"


def test_t10fix3_184_marca_bloqueada_no_ordena_retirarla(tmp_path, monkeypatch):
    """#184/N8: una marca VALIDA bloqueada (antivirus, backup) con plazo de sobra: agotar los reintentos
    por `PermissionError` da «bloqueada por otro proceso o sin permisos: vuelve a pasar /doctor…», NUNCA
    el remedio de retirarla; igual en `_escribir_marca` (el siguiente ensamblado la reescribe) y con el
    `OSError` del `lstat`. Windows: bloqueo REAL (`CreateFileW`, share 0); POSIX: simulado."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    res = _vigentes(store, raiz)
    ruta = store / "exports" / asm.MARCA
    monkeypatch.setattr(rec, "ESPERA_REINTENTO_S", 0.001)
    soltar = _bloquear_exclusivo(ruta)
    if soltar is None:
        soltar = _sin_permiso_en(monkeypatch, ruta)
    try:
        d = asm.estado_dataset(str(store), res)
        r = _ensamblar(cfg, raiz, escribir=True)
    finally:
        soltar()
    assert d["estado"] == "no_verificable" and "bloqueada por otro proceso o sin permisos" in d["motivo"], d
    assert "vuelve a pasar /doctor" in d["motivo"] and asm.REMEDIO_MARCA not in d["motivo"], d
    assert r["existente"] is True and "bloqueada por otro proceso o sin permisos" in r["aviso_marca"], r["aviso_marca"]
    assert asm.REMEDIO_MARCA not in r["aviso_marca"]
    assert _estado(store, raiz)["estado"] == "al_dia"
    real = rec._stat_sin_seguir

    def lstat_roto(x):
        if os.path.basename(str(x)) == asm.MARCA:
            raise PermissionError(13, "no")
        return real(x)
    monkeypatch.setattr(rec, "_stat_sin_seguir", lstat_roto)
    d = asm.estado_dataset(str(store), res)
    assert "bloqueada por otro proceso o sin permisos" in d["motivo"] and asm.REMEDIO_MARCA not in d["motivo"], d
    for ajena in ("{}", "x" * (asm.TOPE_MARCA + 1)):                     # el remedio queda para una ajena
        monkeypatch.setattr(rec, "_stat_sin_seguir", real)
        ruta.write_text(ajena, encoding="utf-8")
        assert asm.REMEDIO_MARCA in asm.estado_dataset(str(store), res)["motivo"]


def test_t10fix3_186_estado_no_deja_pycache_en_la_skill(tmp_path):
    """#186: `dataset-assembler.py --estado` (solo lectura) sobre una COPIA de la skill no deja ningun
    `__pycache__`: toda carga por ruta de la skill usa `dont_write_bytecode` (restaurado al salir)."""
    copia = tmp_path / "plugin"
    shutil.copytree(HERE, str(copia / "skills" / "training-data-services" / "scripts"),
                    ignore=shutil.ignore_patterns("__pycache__", "test_*"))
    shutil.copytree(os.path.normpath(os.path.join(HERE, "..", "..", "..", "agent-kits", "shared")),
                    str(copia / "agent-kits" / "shared"), ignore=shutil.ignore_patterns("__pycache__", "test_*"))
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    entorno = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    script = copia / "skills" / "training-data-services" / "scripts" / "dataset-assembler.py"
    r = subprocess.run([sys.executable, str(script), "--estado", "--project-root", raiz], capture_output=True,
                       text=True, encoding="utf-8", env=entorno, timeout=120)
    assert r.returncode == 0, r.stderr
    caches = [os.path.relpath(b, str(copia)) for b, _d, _f in os.walk(str(copia)) if b.endswith("__pycache__")]
    assert caches == [], caches


def test_t10fix3_186_toda_carga_por_ruta_de_la_skill_usa_dont_write_bytecode():
    """#186: cada funcion de un script de la skill (no test) que ejecuta un modulo por ruta
    (`exec_module`) pone `sys.dont_write_bytecode` y lo restaura (`finally`)."""
    import ast
    vistos = 0
    for fichero in sorted(os.listdir(HERE)):
        if not fichero.endswith(".py") or fichero.startswith("test_"):
            continue
        fuente = open(os.path.join(HERE, fichero), encoding="utf-8").read()
        for nodo in ast.walk(ast.parse(fuente)):
            if isinstance(nodo, ast.FunctionDef) and "exec_module" in (ast.get_source_segment(fuente, nodo) or ""):
                cuerpo = ast.get_source_segment(fuente, nodo)
                vistos += 1
                assert "dont_write_bytecode" in cuerpo and "finally" in cuerpo, (fichero, nodo.name)
    assert vistos >= 3, vistos


def test_t10fix3_n9_con_omisiones_exit_1_texto_y_ayudas(tmp_path, capsys):
    """N9: `con_omisiones` entra en `EXIT_ESTADO` (exit 1), `TEXTO_DATASET` y las ayudas de `--estado`
    (docstring del modulo y `--help`)."""
    assert asm.EXIT_ESTADO["con_omisiones"] == 1 and "con_omisiones" in asm.TEXTO_DATASET
    raiz, cfg, store = _store_basico(tmp_path)
    (store / "cases" / "a.x" / "v001" / "trajectory.jsonl").write_text("{roto\n", encoding="utf-8")
    _ensamblar(cfg, raiz, escribir=True)
    capsys.readouterr()
    assert asm.main(["--estado", "--project-root", raiz]) == 1
    assert f"dataset: {asm.TEXTO_DATASET['con_omisiones']}" in capsys.readouterr().out
    assert asm.main(["--estado", "--json", "--project-root", raiz]) == 1
    assert json.loads(capsys.readouterr().out)["dataset"]["estado"] == "con_omisiones"
    with pytest.raises(SystemExit):
        asm.main(["--help"])
    ayuda = capsys.readouterr().out
    assert "con omisiones" in " ".join(ayuda.split()) and "con omisiones" in asm.__doc__, ayuda


def test_t10fix3_186_cada_cargador_de_la_skill_carga_sin_bytecode_y_restaura(tmp_path, monkeypatch):
    """#186 (el mutante que el test estatico no veia): CADA cargador por ruta de la skill —el del
    ensamblador, el del recorder (`_cargar_por_ruta`, tambien `cargar_redact`) y el del puente— ejecuta
    el modulo con `sys.dont_write_bytecode` = True y lo deja como estaba al salir, aunque se le llame
    directamente (sin otro cargador por encima que ya lo hubiera puesto)."""
    for nombre in ("espia.py", "redact.py"):
        (tmp_path / nombre).write_text("import sys\nVISTO = sys.dont_write_bytecode\n", encoding="utf-8")
    pfc = _load("propose-from-case.py", "tds_pfc_186")
    espia = str(tmp_path / "espia.py")
    monkeypatch.setattr(sys, "dont_write_bytecode", False)
    cargadores = {"asm._cargar": lambda: asm._cargar(espia, "tds_espia_asm"),
                  "rec._cargar_por_ruta": lambda: rec._cargar_por_ruta("tds_espia_rec", espia),
                  "rec.cargar_redact": lambda: rec.cargar_redact([str(tmp_path)]),
                  "pfc._cargar": lambda: pfc._cargar(espia, "tds_espia_pfc")}
    for que, cargar in cargadores.items():
        mod = cargar()
        assert mod.VISTO is True, que
        assert sys.dont_write_bytecode is False, que


# ------------------------------------------------------------------ T-10 fix4 (#189, #190, #191, #196)

def test_t10fix4_189_referencia_con_espacio_b1_literal(tmp_path):
    """#189 (B1 literal): con `family_pattern "[a-z ]+"`, un Gold de `family="a b"` omitido (se renombra su
    `trajectory.jsonl`) deja una marca que su propio lector ACEPTA (la referencia se valida como un
    `case_id`, no con `\\S`) -> `con_omisiones` -> restaurar -> sigue `con_omisiones` -> reensamblar ->
    `al_dia` (antes: la marca no se publicaba y la frescura salia `no_verificable`)."""
    raiz, cfg, store = _proyecto(tmp_path, ids={"family_pattern": "[a-z ]+"})
    _grabar(cfg, raiz, family="a b", variant="x", request="pieza con espacio en la familia y dos ranuras")
    _grabar(cfg, raiz, family="bench", variant="x", request="engranaje de doce dientes con eje de acero")
    tr = store / "cases" / "a b.x" / "v001" / "trajectory.jsonl"
    aparte = tr.with_name("trajectory.jsonl.aparte")
    tr.rename(aparte)
    r = _ensamblar(cfg, raiz, escribir=True)
    assert r["aviso_marca"] is None, r["aviso_marca"]
    m = _marca(store)
    assert m["omitidos"] == 1 and m["omitidos_muestra"] == [dict(OMISION_OK, ref="geo-a b.x@v001")], m
    d = _estado(store, raiz)
    assert d["estado"] == "con_omisiones" and "geo-a b.x@v001" in d["motivo"], d
    aparte.rename(tr)
    assert _estado(store, raiz)["estado"] == "con_omisiones"
    _ensamblar(cfg, raiz, escribir=True)
    assert _estado(store, raiz)["estado"] == "al_dia"


def test_t10fix4_189_la_muestra_solo_guarda_lo_que_su_lector_acepta():
    """#189 (a)+(b): el lector valida `<case_id>@v<N>` con la regla de un `case_id` (`rpartition("@v")`,
    `_motivo_case_id` sin `id_prefix`: longitud; sin controles ni formato Unicode) y `_muestra` usa la
    MISMA regla (fuente unica): lo que el lector rechazaria no entra en la muestra."""
    tope = asm.cs.CASE_ID_MAX
    buenas = ("geo-a b.x@v001", "a.x@v1", "geo-ñandú.x@v123456789", "x" * tope + "@v001", "a@vb.x@v002")
    malas = ("geo-a.x", "@v001", "geo-a.x@v", "geo-a.x@v0x1", "geo-a.x@v1234567890", "x" * (tope + 1) + "@v001",
             "geo-‮a.x@v001", "geo-a\x1b.x@v001", "geo-a .x@v001", "geo-a​.x@v001", "geo-a\t.x@v001",
             "geo-a.x@v١", "geo-a.x@v+1", "geo-a.x@v 1", 7)
    for ref in buenas:
        assert asm._motivo_referencia(ref) is None, ref
        assert asm._motivo_omisiones(1, [dict(OMISION_OK, ref=ref)]) is None, ref
    for ref in malas:
        assert asm._motivo_referencia(ref) is not None, ref
        assert asm._motivo_omisiones(1, [dict(OMISION_OK, ref=ref)]) is not None, ref
    lista = [dict(OMISION_OK, ref=ref) for ref in ("geo-‮a.x@v001", "geo-a b.x@v001", "geo-a​.x@v002")]
    assert asm._muestra(lista) == [dict(OMISION_OK, ref="geo-a b.x@v001")]


def test_t10fix4_189_c_marca_que_no_se_publica_no_promete_reescribirse(tmp_path, monkeypatch):
    """#189 (c): si la marca que se iba a escribir no pasaria su lector, el aviso NO promete «el
    siguiente ensamblado la reescribe»: dice que la frescura sigue con la marca anterior."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    monkeypatch.setattr(asm, "_bytes_marca", lambda m: b'{"version": 1}\n')
    r = _ensamblar(cfg, raiz, escribir=True)
    assert "no se publica" in r["aviso_marca"] and "reescribe" not in r["aviso_marca"], r["aviso_marca"]
    assert "anterior" in r["aviso_marca"], r["aviso_marca"]


def _cambiar_id_prefix(raiz, cfg, prefijo):
    nueva = dict(cfg, id_prefix=prefijo)
    ruta = os.path.join(raiz, ".claude", "knowledge-services", "training.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(nueva, f)
    return nueva


def test_t10fix4_190_otro_id_prefix_es_la_causa_primera_en_estado_y_en_el_rechazo(tmp_path, capsys):
    """#190 (escenario literal): con un store existente y el `id_prefix` de training.json cambiado, la
    causa «N versiones con otro `id_prefix`…: restauralo o usa otro `root`» va PRIMERO en la frescura
    (`--estado`, exit 1: precede al mensaje de #183) y en el rechazo del ensamblador."""
    raiz, cfg, store = _store_basico(tmp_path)
    _ensamblar(cfg, raiz, escribir=True)
    nueva = _cambiar_id_prefix(raiz, cfg, "nuevo")
    res = rec.resumen_store(str(store), raiz, id_prefix="nuevo")
    assert res["otro_prefijo"] == 6 and res["n_gold"] == 0, res
    d = asm.estado_dataset(str(store), res)
    causa = "6 versiones con otro `id_prefix` que el de training.json: restauralo o usa otro `root`"
    assert d["estado"] == "con_omisiones" and d["motivo"].startswith(causa), d
    assert "0 Gold vigentes" not in d["motivo"], d
    capsys.readouterr()
    assert asm.main(["--estado", "--project-root", raiz]) == 1
    assert f"dataset: {asm.TEXTO_DATASET['con_omisiones']} ({causa}" in capsys.readouterr().out
    with pytest.raises(rec.Rechazo) as e:
        asm.ensamblar(nueva, raiz, {"bench"}, fecha=FECHA)
    assert e.value.mensaje.startswith(causa), e.value.mensaje
    r = _cli("--benchmark", "bench", "--project-root", raiz)
    assert r.returncode == 1 and r.stderr.startswith(f"rechazado: {causa}"), r.stderr[-2000:]
    _cambiar_id_prefix(raiz, cfg, "geo")
    assert asm.estado_dataset(str(store), rec.resumen_store(str(store), raiz, id_prefix="geo"))["estado"] == "al_dia"


def test_t10fix4_191_validation_ilegible_nunca_es_al_dia(tmp_path, monkeypatch):
    """#191: un Gold con `validation.json` ilegible por una causa PERMANENTE (`chmod 000` REAL en POSIX
    sin root; si no, `PermissionError` simulado con `_PERMISOS_PERMANENTES`) no se sabe si es Gold: con la
    firma igual, `con_omisiones` con la causa primero, exit 1; nunca `al_dia`."""
    import errno as _errno
    raiz, cfg, store = _store_basico(tmp_path)
    val = store / "cases" / "a.x" / "v002" / "validation.json"
    real_chmod = os.name != "nt" and hasattr(os, "geteuid") and os.geteuid() != 0
    if real_chmod:
        assert rec._PERMISOS_PERMANENTES
        os.chmod(str(val), 0)
        devolver = lambda: os.chmod(str(val), 0o644)                     # noqa: E731
    else:
        monkeypatch.setattr(rec, "_PERMISOS_PERMANENTES", True)
        devolver = _sin_permiso_en(monkeypatch, val, _errno.EACCES)
    try:
        _ensamblar(cfg, raiz, escribir=True)
        res = _vigentes(store, raiz)
        assert res["validacion_ilegible"] == 1 and res["transitorias"] == 0, res
        d = asm.estado_dataset(str(store), res)
        causa = "1 version con validation.json ilegible: no se sabe si es Gold (revisa los permisos)"
        assert d["estado"] == "con_omisiones" and d["motivo"].startswith(causa), d
        assert asm.main(["--estado", "--project-root", raiz]) == 1
    finally:
        devolver()
    assert _estado(store, raiz)["estado"] == "desactualizado"          # legible otra vez: un Gold mas
    _ensamblar(cfg, raiz, escribir=True)
    assert _estado(store, raiz)["estado"] == "al_dia"


def _medir(fn):
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def test_t10fix4_196_marca_con_benchmark_enorme_como_mucho_3_serializaciones(monkeypatch):
    """#196: con un `benchmark` de 10^5 familias y una muestra de 10, `_bytes_marca` resume el benchmark
    ANTES de recortar la muestra (la muestra cabe entera) y serializa la marca como mucho 3 veces (antes:
    hasta 11 serializaciones enteras bajo `exports/.lock`); tarda < 2x una serializacion de la marca. Si
    lo que no cabe es la muestra, se recorta de una vez (bytes por entrada) y el benchmark se conserva."""
    bench = [f"familia{i:06d}" for i in range(10 ** 5)]
    muestra = [dict(OMISION_OK, ref=f"geo-a.x@v{i:03d}") for i in range(1, 11)]
    marca = dict(MARCA_OK, parametros=dict(PARAMETROS_OK, benchmark=bench), omitidos=10, omitidos_muestra=muestra)
    real = json.dumps
    vistas = []

    def espia(obj, *a, **kw):
        if isinstance(obj, dict) and "firma" in obj:
            vistas.append(1)
        return real(obj, *a, **kw)

    def contar(m):
        vistas.clear()
        monkeypatch.setattr(asm.json, "dumps", espia)
        try:
            return asm._bytes_marca(m)
        finally:
            monkeypatch.setattr(asm.json, "dumps", real)
    datos = contar(marca)
    leida = json.loads(datos)
    assert len(datos) <= asm.TOPE_MARCA and asm._motivo_marca(leida) is None, len(datos)
    assert len(vistas) <= 3, len(vistas)
    assert leida["parametros"]["benchmark"] == "100000 familias" and leida["omitidos_muestra"] == muestra, leida
    base = min(_medir(lambda: asm._serializar_marca(marca)) for _ in range(5))
    nuevo = min(_medir(lambda: asm._bytes_marca(marca)) for _ in range(5))
    assert nuevo < 2 * base, (nuevo, base)
    largas = [dict(OMISION_OK, ref="ñ" * 190 + f"@v{i:03d}") for i in range(10)]
    datos = contar(dict(MARCA_OK, omitidos=11, omitidos_muestra=largas))
    leida = json.loads(datos)
    assert len(vistas) <= 3 and len(datos) <= asm.TOPE_MARCA and asm._motivo_marca(leida) is None
    k = len(leida["omitidos_muestra"])
    assert leida["parametros"] == PARAMETROS_OK and 0 < k < 10 and leida["omitidos_muestra"] == largas[:k], leida
    siguiente = len(real(largas[k], ensure_ascii=True, sort_keys=True)) + 2
    assert len(datos) + siguiente > asm.TOPE_MARCA                           # recorta lo justo, de una vez
    for n in range(20, 200):                                                 # la cuenta exacta, en cada frontera
        refs = [dict(OMISION_OK, ref="ñ" * n + f"@v{i:03d}") for i in range(10)]
        datos = asm._bytes_marca(dict(MARCA_OK, omitidos=10, omitidos_muestra=refs))
        k = len(json.loads(datos)["omitidos_muestra"])
        assert len(datos) <= asm.TOPE_MARCA, (n, len(datos))
        if k < 10:
            assert len(datos) + len(real(refs[k], ensure_ascii=True, sort_keys=True)) + 2 > asm.TOPE_MARCA, n
