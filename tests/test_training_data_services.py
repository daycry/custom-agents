#!/usr/bin/env python3
"""Suite de REPO de `training-data-services` (T-11): aislamiento, anti-leakage y cero impacto.

Las suites de la skill (`skills/training-data-services/scripts/test_*.py`) prueban cada script por
dentro; esta prueba las INVARIANTES que cruzan piezas, contra el pipeline real:
  - ningún binario inline entra en un caso ni sale en un export (design.md «Que NO hace el plugin»);
  - solo Gold humano ATADO a su contenido llega a `train.jsonl`/`benchmark.jsonl` (CA-03, #132);
  - una sola dirección: nada de `docs/knowledge/` alimenta el case store ni el dataset (spec
    «Relacion con las otras dos iniciativas», anti-leakage), ni el store puede vivir dentro (ADR-019);
  - CA-01: sin `training.json` o con `enabled: false`, el ciclo es idéntico (capabilities, /doctor,
    knowledge-find, y ningún script compartido del ciclo lee `training.json`);
  - CA-08: la skill no entrena, no sirve ni corre benchmarks (sin `subprocess` ni red);
  - CA-04: el plugin no tiene métricas de dominio (`metrics` es opaco: solo se valida la forma).
Ejecutar: python3 -m pytest -q tests/test_training_data_services.py (la CI también lo lanza como
script: `python tests/test_training_data_services.py`).
"""
import builtins
import copy
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys

try:
    import pytest
except ImportError:  # el bucle de la CI ejecuta el fichero como script; sin pytest solo informa
    pytest = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "training-data-services")
SCRIPTS = os.path.join(SKILL, "scripts")
SHARED = os.path.join(ROOT, "agent-kits", "shared")


def _load(ruta, nombre):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


asm = _load(os.path.join(SCRIPTS, "dataset-assembler.py"), "tds_asm_repo")
rec = asm.rec
cs = rec.cs
cap_mod = _load(os.path.join(SHARED, "capabilities.py"), "capabilities_repo")
doctor = _load(os.path.join(SHARED, "doctor.py"), "doctor_repo")

FECHA = "20260928"
CASO = {
    "family": "ramp", "variant": "steep", "request": "Genera una rampa de 30 grados",
    "context": {"text": "escena vacia"}, "constraints": {"max_angle_deg": 30}, "metrics": {"score": 0.5},
    "outcome": "success",
    "trajectory": [{"role": "user", "content": "Genera una rampa"},
                   {"role": "assistant", "content": "", "tool_calls": [{"name": "make_ramp", "arguments": {"a": 30}}]},
                   {"role": "tool", "name": "make_ramp", "content": "ok"},
                   {"role": "assistant", "content": "Hecho."}],
    "artifacts": [{"path": "final/ramp.blend", "hash": "sha256:ab12", "kind": "mesh"}],
}
CLAVES_LINEA = {"messages", "ref", "case_id", "version", "family", "variant", "outcome", "supersedes_case"}
CLAVES_TURNO = {"role", "content", "tool_calls", "name"}


def _texto_propio(semilla, n=40):
    """Texto determinista y DISTINTO por caso (palabras de un sha256): casos distintos no son
    near-duplicates para `dedup.py` y el ensamblador no descarta ninguno por cruce."""
    h = hashlib.sha256(semilla.encode("utf-8")).hexdigest() * 4
    return " ".join(h[i:i + 5] for i in range(0, n * 5, 5))


def _caso(family, variant="x", **cambios):
    c = copy.deepcopy(CASO)
    c.update(family=family, variant=variant, case_id=f"geo-{family}.{variant}",
             request=_texto_propio(f"req-{family}.{variant}"))
    c["trajectory"][0]["content"] = _texto_propio(f"user-{family}.{variant}")
    c["trajectory"][3]["content"] = _texto_propio(f"fin-{family}.{variant}")
    c.update(cambios)
    return c


def _proyecto(tmp_path, enabled=True):
    raiz = tmp_path / "proj"
    raiz.mkdir(parents=True, exist_ok=True)
    cfg = {"version": 1, "enabled": enabled, "root": "../store", "id_prefix": "geo"}
    d = raiz / ".claude" / "knowledge-services"
    d.mkdir(parents=True, exist_ok=True)
    (d / "training.json").write_text(json.dumps(cfg), encoding="utf-8")
    return str(raiz), cfg, tmp_path / "store"


def _gold(cfg, raiz, family, variant="x", **cambios):
    r = rec.grabar(_caso(family, variant, **cambios), cfg, raiz)
    rec.cambiar_estado(r["case_id"], r["version"], "approved", cfg, raiz, approved_by_human=True)
    return r


def _lineas_export(ruta):
    out = []
    for f in asm.JSONL:
        with open(os.path.join(ruta, f), encoding="utf-8") as fh:
            out += [json.loads(l) for l in fh.read().splitlines()]
    return out


def _bytes_export(ruta):
    todo = b""
    for base, _dirs, fs in os.walk(ruta):
        for f in sorted(fs):
            with open(os.path.join(base, f), "rb") as fh:
                todo += fh.read()
    return todo


def _no_skill_scripts():
    return sorted(os.path.join(SCRIPTS, f) for f in os.listdir(SCRIPTS)
                  if f.endswith(".py") and not f.startswith("test_"))


# ------------------------------------------------------------------ binarios inline

def test_ningun_binario_inline_entra_en_un_caso(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    for clave in cs.CLAVES_INLINE:
        arts = [{"path": "final/x.bin", "hash": "sha256:ab", "kind": "mesh", clave: "AAECAwQ="}]
        with pytest.raises(rec.Rechazo):
            rec.grabar(_caso("a", artifacts=arts), cfg, raiz)
    assert not (store / "cases").exists() or not os.listdir(str(store / "cases"))


def test_ningun_binario_ni_metrica_sale_en_un_export(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    _gold(cfg, raiz, "a")
    _gold(cfg, raiz, "bench")
    r = asm.ensamblar(cfg, raiz, {"bench"}, fecha=FECHA)
    lineas = _lineas_export(r["ruta"])
    assert len(lineas) == 2
    for l in lineas:
        assert set(l) <= CLAVES_LINEA, set(l) - CLAVES_LINEA
        for t in l["messages"]:
            assert set(t) <= CLAVES_TURNO and isinstance(t.get("content", ""), str)
    crudo = _bytes_export(r["ruta"])
    assert b"sha256:ab12" not in crudo and b"ramp.blend" not in crudo and b'"score"' not in crudo
    assert sorted(os.listdir(r["ruta"])) == ["benchmark.jsonl", "manifest.json", "train.jsonl"]


# ------------------------------------------------------------------ solo Gold humano atado

def test_ningun_no_gold_ni_gold_sin_atar_llega_al_dataset(tmp_path):
    raiz, cfg, store = _proyecto(tmp_path)
    buenos = {_gold(cfg, raiz, "a")["case_id"], _gold(cfg, raiz, "bench")["case_id"]}
    for fam, estado in (("p", None), ("n", "needs_changes"), ("r", "rejected")):
        r = rec.grabar(_caso(fam), cfg, raiz)
        if estado:
            rec.cambiar_estado(r["case_id"], r["version"], estado, cfg, raiz)
    # Gold cuyo contenido cambió DESPUÉS de aprobarlo: content_hash no casa -> fuera
    t = _gold(cfg, raiz, "t")
    req = os.path.join(t["path"], "request.json")
    with open(req, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({"request": "otra peticion distinta"}) + "\n")
    # `approved` escrito a mano sin humano: incoherente -> fuera
    f = rec.grabar(_caso("f"), cfg, raiz)
    with open(os.path.join(f["path"], "validation.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"status": "approved", "approved_by_human": False, "approved_at": None,
                             "reviewer_note": None}) + "\n")
    # el índice MIENTE (todo approved): no cuenta
    with open(os.path.join(str(store), rec.INDICE), "a", encoding="utf-8") as fh:
        for fam in ("p", "n", "r", "f"):
            fh.write(json.dumps({"case_id": f"geo-{fam}.x", "version": 1, "family": fam, "variant": "x",
                                 "status": "approved", "outcome": "success",
                                 "updated_at": "2026-09-28T00:00:00Z"}) + "\n")
    r = asm.ensamblar(cfg, raiz, {"bench"}, fecha=FECHA)
    assert {l["case_id"] for l in _lineas_export(r["ruta"])} == buenos
    motivos = {c["case_id"]: c["motivo"] for c in r["manifest"]["casos"] if c["particion"] is None}
    assert motivos["geo-t.x"] == asm.MOTIVO_SIN_ATAR
    assert set(motivos) == {"geo-p.x", "geo-n.x", "geo-r.x", "geo-t.x"}
    # el `approved` sin humano ni siquiera es una version valida: el recorrido la omite con aviso
    assert "geo-f.x" not in {c["case_id"] for c in r["manifest"]["casos"]}
    assert any("cases/f.x/v001" in a and "incoherente" in a for a in r["avisos_store"]), r["avisos_store"]


# ------------------------------------------------------------------ una sola dirección (anti-leakage)

# #158: `builtins.open` y `io.open` son el MISMO objeto pero dos atributos: `pathlib.Path.read_text`
# llama a `io.open`, así que parchear solo `builtins.open` dejaba vivo un lector por `pathlib`.
ACCESOS_ESPIADOS = ((builtins, "open"), (io, "open"), (os, "open"), (os, "scandir"), (os, "listdir"),
                    (os, "stat"), (os, "lstat"))


def _espiar_accesos(monkeypatch):
    """Lista (viva) de las rutas que se abren, listan o examinan mientras el espía está puesto."""
    abiertos = []
    for modulo, nombre in ACCESOS_ESPIADOS:
        original = getattr(modulo, nombre)

        def _espia(ruta, *a, _o=original, _stat=nombre in ("stat", "lstat"), **k):
            if isinstance(ruta, (str, bytes, os.PathLike)):
                abiertos.append((_stat, os.fsdecode(ruta)))
            return _o(ruta, *a, **k)
        monkeypatch.setattr(modulo, nombre, _espia)
    return abiertos


def _tocados(abiertos, dk):
    """Accesos a `docs/knowledge/`: abrir o listar el directorio o algo de dentro, o examinar (`stat`)
    algo de DENTRO. Examinar el propio `docs/knowledge` no lee nada: es la contención de ADR-019 (el
    `realpath` de POSIX hace `lstat` de cada componente para comprobar que el store no vive ahí)."""
    dk_canon = os.path.normcase(os.path.realpath(dk))
    out = []
    for es_stat, p in abiertos:
        canon = os.path.normcase(os.path.realpath(os.path.abspath(p)))
        if canon.startswith(dk_canon + os.sep) or (canon == dk_canon and not es_stat):
            out.append(p)
    return out


def test_158_el_espia_ve_lecturas_por_pathlib_y_por_stat(tmp_path, monkeypatch):
    """#158: el espía del anti-leakage no se deja fuera `pathlib` (`io.open`) ni `os.stat`/`os.lstat`."""
    import pathlib
    dk = tmp_path / "docs" / "knowledge" / "approved"
    dk.mkdir(parents=True)
    (dk / "k.md").write_text("TOKEN-CURADO-7f3a\n", encoding="utf-8")
    for lector in (lambda: pathlib.Path(str(dk / "k.md")).read_text(encoding="utf-8"),
                   lambda: os.stat(str(dk / "k.md")), lambda: os.lstat(str(dk / "k.md"))):
        abiertos = _espiar_accesos(monkeypatch)
        lector()
        monkeypatch.undo()
        assert _tocados(abiertos, str(tmp_path / "docs" / "knowledge")), "el espía no vio el acceso"


def test_el_case_store_no_puede_vivir_en_docs_knowledge(tmp_path):
    raiz = tmp_path / "proj"
    (raiz / "docs" / "knowledge").mkdir(parents=True)
    for root in ("docs/knowledge/cases", "Docs/Knowledge", str(raiz / "docs" / "knowledge" / "x")):
        cfg = {"version": 1, "enabled": True, "root": root, "id_prefix": "geo"}
        with pytest.raises(rec.Rechazo):
            rec.grabar(_caso("a"), cfg, str(raiz))
        with pytest.raises(rec.Rechazo):
            asm.ensamblar(cfg, str(raiz), {"a"}, fecha=FECHA)
    assert os.listdir(str(raiz / "docs" / "knowledge")) == []


def test_nada_de_docs_knowledge_alimenta_el_store_ni_el_dataset(tmp_path, monkeypatch):
    """El recorder y el ensamblador no ABREN nada bajo `docs/knowledge/` (ni aprobado, ni candidatos,
    ni ADR) y ningún texto curado aparece en el store ni en el export."""
    raiz, cfg, store = _proyecto(tmp_path)
    dk = os.path.join(raiz, "docs", "knowledge")
    for sub, nombre in (("approved", "k.md"), ("candidates/pending", "c.md"), ("adr", "ADR-001-x.md")):
        os.makedirs(os.path.join(dk, sub), exist_ok=True)
        with open(os.path.join(dk, sub, nombre), "w", encoding="utf-8") as f:
            f.write("TOKEN-CURADO-7f3a rampa de 30 grados con bola roja\n")
    abiertos = _espiar_accesos(monkeypatch)
    _gold(cfg, raiz, "a")
    _gold(cfg, raiz, "bench")
    r = asm.ensamblar(cfg, raiz, {"bench"}, fecha=FECHA)
    monkeypatch.undo()
    assert _tocados(abiertos, dk) == [], _tocados(abiertos, dk)
    assert abiertos, "el espía no vio ninguna apertura"
    assert b"TOKEN-CURADO-7f3a" not in _bytes_export(str(store))


# ------------------------------------------------------------------ CA-01: cero impacto

def _knowledge_find(proj):
    r = subprocess.run([sys.executable, os.path.join(SHARED, "knowledge-find.py"), "--root", proj,
                        "--no-index", "--json", "rampa"], capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=120)
    return r.returncode, r.stdout, r.stderr


def _doctor_sin_training(proj):
    inf = doctor.diagnostico(proj)
    lineas = [(b["clave"], l["estado"], l["que"], l["detalle"].replace(proj, "<P>"))
              for b in inf["bloques"] for l in b["lineas"] if l["que"] != "training"]
    return inf["exit"], lineas


def test_ca01_sin_training_json_o_desactivado_el_ciclo_es_identico(tmp_path):
    base = tmp_path / "a" / "proj"
    base.mkdir(parents=True)
    (base / ".claude").mkdir()
    apagado, _cfg, _store = _proyecto(tmp_path / "b", enabled=False)
    otras = lambda p: [(c["id"], c["enabled"], json.dumps(c["health"], sort_keys=True))
                       for c in cap_mod.enumerar(p) if c["id"] != "training"]
    assert otras(str(base)) == otras(apagado)
    for p in (str(base), apagado):
        t = next(c for c in cap_mod.enumerar(p) if c["id"] == "training")
        assert t["enabled"] is False and t["health"] == {"estado": "deshabilitado"}
    assert [l for l in doctor.bloque_capacidades(None, str(base))["lineas"] if l["que"] == "training"] == []
    e1, l1 = _doctor_sin_training(str(base))
    e2, l2 = _doctor_sin_training(apagado)
    assert e1 == e2 and [x for x in l1 if x[0] != "configs"] == [x for x in l2 if x[0] != "configs"]
    k1, k2 = _knowledge_find(str(base)), _knowledge_find(apagado)
    assert k1[0] == k2[0] and k1[1].replace(str(base), "<P>") == k2[1].replace(apagado, "<P>")
    assert not (tmp_path / "b" / "store").exists()


def test_ca01_ningun_script_del_ciclo_lee_training_json():
    """Solo el registro de capacidades conoce `training.json`; el resto de `agent-kits/shared/` (ciclo,
    hooks, brief, progreso, journal, knowledge-find) no lo nombra (los comentarios de #139 no cuentan)."""
    permitidos = {"capabilities.py", "test_capabilities.py"}
    for f in sorted(os.listdir(SHARED)):
        if not f.endswith(".py") or f in permitidos or f.startswith("test_"):
            continue
        with open(os.path.join(SHARED, f), encoding="utf-8") as fh:
            texto = fh.read()
        assert "training.json" not in texto and "case-recorder" not in texto and "dataset-assembler" not in texto, f
    with open(os.path.join(SHARED, "doctor.py"), encoding="utf-8") as fh:
        assert "training" not in fh.read()
    # #160: la CA nombra también `skills/knowledge-services/` (y los hooks corren en cada sesión)
    vistos = 0
    for base in (os.path.join(ROOT, "skills", "knowledge-services"), os.path.join(ROOT, "hooks")):
        for d, dirs, fs in os.walk(base):
            dirs[:] = [x for x in dirs if x != "__pycache__"]
            for f in fs:
                if f.startswith("test_") or not f.endswith((".py", ".sh", ".js", ".json")):
                    continue
                with open(os.path.join(d, f), encoding="utf-8") as fh:
                    texto = fh.read()
                vistos += 1
                for prohibido in ("training.json", "case-recorder", "dataset-assembler"):
                    assert prohibido not in texto, (os.path.relpath(os.path.join(d, f), ROOT), prohibido)
    assert vistos >= 10, vistos


# ------------------------------------------------------------------ CA-08 y CA-04

PROHIBIDO_EJECUCION = ("import subprocess", "subprocess.", "os.system", "os.popen", "os.exec", "os.spawn",
                       "import socket", "urllib", "http.client", "import requests", "multiprocessing")


def test_ca08_la_skill_no_entrena_ni_sirve_ni_ejecuta_nada():
    scripts = _no_skill_scripts()
    assert len(scripts) >= 5, scripts
    for ruta in scripts:
        with open(ruta, encoding="utf-8") as f:
            texto = f.read()
        for p in PROHIBIDO_EJECUCION:
            assert p not in texto, (os.path.basename(ruta), p)
        codigo = "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("#"))
        for p in ("ollama", "fine_tune", "fine-tune", "torch", "transformers", "peft"):
            assert not re.search(rf"\bimport\s+{re.escape(p)}|\b{re.escape(p)}\s*\(", codigo, re.I), (ruta, p)


def test_ca04_metrics_es_opaco_el_plugin_no_tiene_metricas_de_dominio(tmp_path):
    """Dos casos que solo difieren en `metrics` (cualquier forma de objeto) se validan, graban, aprueban
    y exportan igual: el plugin no lee ninguna métrica; una que no es objeto es error de FORMA."""
    raiz, cfg, store = _proyecto(tmp_path)
    raras = ({}, {"score": -1e9}, {"slope_deg": "muy empinada", "nested": {"a": [1, 2, {"b": None}]}})
    for i, m in enumerate(raras):
        _gold(cfg, raiz, f"m{i}", metrics=m)
    _gold(cfg, raiz, "bench")
    for no_objeto in ([1, 2], "0.5", 3):
        with pytest.raises(rec.Rechazo) as e:
            rec.grabar(_caso("z", metrics=no_objeto), cfg, raiz)
        assert [x["campo"] for x in e.value.errores] == ["metrics"], e.value.errores
    r = asm.ensamblar(cfg, raiz, {"bench"}, fecha=FECHA)
    exportados = sorted(l["case_id"] for l in _lineas_export(r["ruta"]))
    assert exportados == sorted(["geo-bench.x"] + [f"geo-m{i}.x" for i in range(len(raras))])
    for ruta in _no_skill_scripts():
        with open(ruta, encoding="utf-8") as f:
            codigo = f.read()
        # ninguna LECTURA de un campo de `metrics` (`caso["metrics"]["x"]`, `…["metrics"].get(`,
        # `metrics.get(`) ni herramienta de dominio (`bpy`): el plugin solo comprueba que es un objeto
        assert not re.search(r"""\[\s*["']metrics["']\s*\]\s*(\[|\.get\()|metrics\.get\(|\bbpy\b""", codigo), ruta


# ------------------------------------------------------------------ CONTRACTS.md: la Puerta de cada arista casa

ARISTAS = ("E20", "E21", "E22", "E23", "E24")
RUTA_PY = r"(?:skills|agent-kits|tests)/[\w./-]+\.py"


def _defs_de(ruta):
    with open(ruta, encoding="utf-8") as f:
        return set(re.findall(r"^def (test_\w+)", f.read(), re.M))


def _celdas(fila):
    """Celdas de una fila de tabla Markdown, sin partir por un `\\|` escapado dentro de una celda."""
    return [c.replace("\x00", "|") for c in fila.replace("\\|", "\x00").split("|")[1:-1]]


def test_las_aristas_de_la_skill_tienen_una_puerta_que_casa_con_los_tests():
    """Cada arista de `training-data-services` en `docs/agents/CONTRACTS.md` (E20-E24) tiene Puerta, y
    lo que la Puerta cita existe HOY: los ficheros, los tests nombrados (o un prefijo `…_*` que casa con
    alguno) y cada filtro `-k` selecciona al menos un test de lo citado (fichero o carpeta)."""
    with open(os.path.join(ROOT, "docs", "agents", "CONTRACTS.md"), encoding="utf-8") as f:
        filas = {l.split(" · ", 1)[0][2:]: l for l in f.read().splitlines() if re.match(r"\| E\d+ · ", l)}
    for arista in ARISTAS:
        assert arista in filas, arista
        celdas = _celdas(filas[arista])
        assert len(celdas) == 9, (arista, len(celdas))
        puerta = celdas[7]
        ficheros = re.findall(RUTA_PY, puerta)
        carpetas = re.findall(r"(?:skills|agent-kits|tests)/[\w./-]*[\w-](?=[\s`])(?<!\.py)", puerta)
        assert ficheros or carpetas, (arista, puerta)
        defs = set()
        for rel in ficheros:
            assert os.path.isfile(os.path.join(ROOT, rel)), (arista, rel)
            if os.path.basename(rel).startswith("test_"):
                defs |= _defs_de(os.path.join(ROOT, rel))
        for rel in carpetas:
            base = os.path.join(ROOT, rel)
            assert os.path.isdir(base), (arista, rel)
            for f in os.listdir(base):
                if f.startswith("test_") and f.endswith(".py"):
                    defs |= _defs_de(os.path.join(base, f))
        propios = {os.path.basename(x)[:-3] for x in ficheros}
        for nombre in set(re.findall(r"\btest_\w+\*?", puerta)) - propios:
            if nombre.endswith(("*", "_")):
                assert any(x.startswith(nombre.rstrip("*")) for x in defs), (arista, nombre)
            else:
                assert nombre in defs, (arista, nombre)
        for filtro in re.findall(r"-k (\w+)", puerta):
            assert any(filtro in x for x in defs), (arista, filtro)


# ------------------------------------------------------------------ #150/#151: el CHANGELOG de la iniciativa

SLUG = "training-data-services"
LEDGER = os.path.join(ROOT, "docs", "roadmap", "2026-09-16-training-data-services", "tasks.md")


def _con_estado_completado(texto):
    """El ledger tal cual, con `estado: completado` en el frontmatter (simula el cierre sin tocarlo)."""
    cabeza, _sep, resto = texto.partition("\n---\n")
    lineas = [l for l in cabeza.split("\n") if not l.startswith("estado:")]
    return "\n".join(lineas + ["estado: completado"]) + "\n---\n" + resto


CABECERAS = {"CHANGELOG.md": f"— `{SLUG}` initiative", "CHANGELOG.es.md": f"— iniciativa `{SLUG}`"}


def _sin_seccion_de_la_iniciativa(texto, fn):
    """#166: el CHANGELOG sin la(s) seccion(es) `### <Categoria> — … `training-data-services` …` que
    `changelog-sync` escribe al cerrar (desde su cabecera hasta la siguiente `###`/`##`): el test es el
    mismo antes y despues del cierre."""
    fuera, saltando = [], False
    for linea in texto.split("\n"):
        if linea.startswith("### ") and CABECERAS[fn] in linea:
            saltando = True
            continue
        if saltando and (linea.startswith("### ") or linea.startswith("## ")):
            saltando = False
        if not saltando:
            fuera.append(linea)
    return "\n".join(fuera)


def _bloques(texto, fn):
    """Las tareas `T-NN` de cada seccion de la iniciativa (categoria -> [T-NN])."""
    out = {}
    for trozo in texto.split("\n### ")[1:]:
        cabecera, _sep, cuerpo = trozo.partition("\n")
        if CABECERAS[fn] in cabecera:
            cuerpo = cuerpo.split("\n## ", 1)[0].split("── ", 1)[0]
            out[cabecera.split(" ", 1)[0]] = re.findall(r"^- \*\*(T-\d+) — ", cuerpo, re.M)
    return out


def _simular_cierre(tmp_path, textos, ledger):
    """Copia (en `tmp_path`) de los dos CHANGELOG `textos` y del ledger con `estado: completado`."""
    for fn, texto in textos.items():
        with open(str(tmp_path / fn), "w", encoding="utf-8", newline="") as f:
            f.write(texto)
    destino = tmp_path / "docs" / "roadmap" / "2026-09-16-training-data-services"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "tasks.md").write_text(_con_estado_completado(ledger), encoding="utf-8")
    script = os.path.join(ROOT, "skills", "changelog-sync", "scripts", "changelog-sync.py")
    return [sys.executable, script, "--root", str(tmp_path), "--only", SLUG]


def _comprobar_11_bajo_added(tmp_path, textos, ledger):
    base = _simular_cierre(tmp_path, {fn: _sin_seccion_de_la_iniciativa(t, fn) for fn, t in textos.items()}, ledger)
    for fn in textos:
        with open(str(tmp_path / fn), encoding="utf-8") as f:
            assert f"`{SLUG}`" not in f.read(), fn            # #150: nada fuera de su seccion cita el slug
    r = subprocess.run(base + ["--dry-run", "--json"], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    pend = json.loads(r.stdout)["pendientes"]
    assert [(p["slug"], p["categoria"], p["tareas"]) for p in pend] == [(SLUG, "Added", 11)], pend
    assert sorted(pend[0]["ficheros"]) == ["CHANGELOG.es.md", "CHANGELOG.md"]
    return base


def test_150_changelog_sync_generaria_las_11_entradas_bajo_added(tmp_path):
    """#150/#151/#166: invariante al cierre. Sobre COPIAS de los dos CHANGELOG (sin la seccion de la
    iniciativa, si ya se escribio) y del ledger con `estado: completado`, `changelog-sync --dry-run
    --only training-data-services --json` da UNA pendiente `Added` con 11 tareas en los dos ficheros
    (nada fuera de su seccion cita el slug entre comillas invertidas; `changelog: added` gana a
    «regresion»). Si los CHANGELOG reales ya tienen la seccion, trae T-01…T-11 bajo `Added`. El ledger
    real no cambia de estado."""
    textos = {}
    for fn in CABECERAS:
        with open(os.path.join(ROOT, fn), encoding="utf-8") as f:
            textos[fn] = f.read()
    with open(LEDGER, encoding="utf-8") as f:
        ledger = f.read()
    assert re.search(r"^changelog:\s*added\b", ledger.split("\n---\n", 1)[0], re.M), "falta `changelog: added`"
    base = _comprobar_11_bajo_added(tmp_path, textos, ledger)
    r = subprocess.run(base + ["--dry-run"], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    for cabecera in (f"### Added — `{SLUG}` initiative", f"### Added — iniciativa `{SLUG}`"):
        bloque = r.stdout.split(cabecera, 1)[1].split("\n### ", 1)[0].split("── ", 1)[0]
        tareas = re.findall(r"^- \*\*(T-\d+) — ", bloque, re.M)
        assert tareas == [f"T-{i:02d}" for i in range(1, 12)], (cabecera, tareas)
    for fn, texto in textos.items():                         # tras el cierre real: su seccion, entera
        if CABECERAS[fn] in texto:
            assert _bloques(texto, fn) == {"Added": [f"T-{i:02d}" for i in range(1, 12)]}, fn


def test_166_el_test_de_150_sigue_pasando_despues_del_cierre(tmp_path):
    """#166: el cierre REAL (`changelog-sync` escribiendo en una copia) no pone en rojo el test de
    #150: tras escribir, la copia trae T-01…T-11 bajo `Added` en los dos CHANGELOG y la misma
    comprobacion (quitando la seccion ya escrita) vuelve a dar las 11 pendientes."""
    textos = {}
    for fn in CABECERAS:
        with open(os.path.join(ROOT, fn), encoding="utf-8") as f:
            textos[fn] = _sin_seccion_de_la_iniciativa(f.read(), fn)
    with open(LEDGER, encoding="utf-8") as f:
        ledger = f.read()
    (tmp_path / "cierre").mkdir()
    base = _simular_cierre(tmp_path / "cierre", textos, ledger)
    r = subprocess.run(base,capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    cerrados = {}
    for fn in CABECERAS:
        with open(str(tmp_path / "cierre" / fn), encoding="utf-8") as f:
            cerrados[fn] = f.read()
        assert _bloques(cerrados[fn], fn) == {"Added": [f"T-{i:02d}" for i in range(1, 12)]}, fn
    (tmp_path / "otra").mkdir()
    _comprobar_11_bajo_added(tmp_path / "otra", cerrados, ledger)


def test_174_el_bullet_de_t11_cuenta_lo_nuevo_de_la_ci(tmp_path):
    """#174: el campo **Changelog** de T-11 nombra lo nuevo de #94: la CI ejecuta tambien las suites de
    `training-data-services` y `knowledge-services` (y un test de repo lo vigila)."""
    with open(LEDGER, encoding="utf-8") as f:
        ledger = f.read()
    t11 = ledger.split("### T-11 - ", 1)[1].split("\n## ", 1)[0]
    campo = re.search(r"^- \*\*Changelog\*\*: (.+)$", t11, re.M).group(1)
    for palabra in ("CI", "training-data-services", "knowledge-services"):
        assert palabra in campo, (palabra, campo)
    assert len(campo) <= 200, len(campo)
    textos = {}
    for fn in CABECERAS:
        with open(os.path.join(ROOT, fn), encoding="utf-8") as f:
            textos[fn] = _sin_seccion_de_la_iniciativa(f.read(), fn)
    base = _simular_cierre(tmp_path, textos, ledger)
    r = subprocess.run(base + ["--dry-run"], capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    bullet = next(l for l in r.stdout.splitlines() if l.startswith("- **T-11 — "))
    assert "CI" in bullet and "knowledge-services" in bullet, bullet


def main():
    if pytest is None:
        print("test_training_data_services: pytest no instalado — suite omitida (pip install pytest)")
        return 0
    return pytest.main(["-q", "-p", "no:cacheprovider", __file__])


if __name__ == "__main__":
    sys.exit(main())
