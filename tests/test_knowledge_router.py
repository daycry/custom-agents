#!/usr/bin/env python3
"""Tests del ROUTER POR CONFIGURACION de `agent-kits/shared/knowledge-find.py` (iniciativa
`graphiti-memory`, T-07): `--intent <nombre>` decide, SOLO con la configuracion declarada en
`.claude/knowledge-services/taxonomy.json` (`backends.<id>.config.router.intents`), si una
consulta se atiende localmente o contra un backend de grafo a traves de su adaptador (CA-12:
ningun LLM decide el enrutado).

Sin red: el backend remoto es un ADAPTADOR STUB escrito en un directorio temporal y cargado por
`backends/__init__.py::cargar_adaptador` (el mismo mecanismo `type -> modulo` que usa
`knowledge-sync.py`), asi que el nucleo de `knowledge-find.py` nunca nombra un backend concreto.

Ejecutar: python -m pytest -q tests/test_knowledge_router.py
"""
import importlib.util
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "agent-kits", "shared", "knowledge-find.py")


def _cargar():
    spec = importlib.util.spec_from_file_location("knowledge_find_router", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kf = _cargar()


# --------------------------------------------------------------- andamiaje

_ACIERTO_REMOTO = {
    "id": "ADR-100", "version": "1", "estado": "aprobado", "evidencia": "validated_case",
    "ruta": "docs/knowledge/approved/adr/ADR-100-grafo.md", "titular": "Decision servida por el grafo",
    "area": "memoria", "categoria": "adr", "fecha": "2026-09-20", "puntuacion": 7,
}

_STUB = '''
"""Adaptador STUB del contrato de knowledge-services para los tests del router."""
import json, os

ACIERTOS = {aciertos}
PUEDE = {puede}
CON_CONSULTA = {con_consulta}
LLAMADAS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llamadas.json")


def health(cfg):
    return {{"estado": "sano"}}


def plan(entries, cfg, force=False):
    return []


def apply(ops, cfg):
    return {{"aplicados": 0}}


def verify(cfg):
    return {{"ok": True}}


def rebuild(entries, cfg):
    return {{"aplicados": 0}}


def revoke(knowledge_id, cfg):
    return None


def puede_leer(cfg):
    return PUEDE


if CON_CONSULTA:
    def consultar(cfg, consulta):
        with open(LLAMADAS, "w", encoding="utf-8") as f:
            json.dump({{"cfg_group_id": cfg.get("group_id"), "consulta": consulta}}, f)
        return {{"aciertos": ACIERTOS}}
'''


def _escribir_stub(directorio, aciertos=None, puede=None, con_consulta=True):
    os.makedirs(directorio, exist_ok=True)
    cuerpo = _STUB.format(
        aciertos=repr([_ACIERTO_REMOTO] if aciertos is None else aciertos),
        puede=repr({"puede": True} if puede is None else puede),
        con_consulta=bool(con_consulta))
    ruta = os.path.join(directorio, "stub.py")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(cuerpo)
    return directorio


def _taxonomia(root, tipo="stub", enabled=True, mode="read", intents=None, extra_config=None):
    cfg = {"mode": mode, "group_id": "proyecto-demo",
           "router": {"intents": {"temporal": True} if intents is None else intents}}
    cfg.update(extra_config or {})
    data = {
        "version": 1,
        "categories": [{"key": "DECISION", "folder": "adr", "min_evidence": "validated_case"}],
        "backends": {"grafo": {"type": tipo, "enabled": enabled, "config": cfg}},
        "evidence_levels": ["observation", "single_case", "validated_case",
                            "multiple_validated_cases", "human_confirmed_rule"],
        "denylist": ["chain-of-thought"],
    }
    destino = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(destino, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    return data


def _corpus_local(root):
    """Una entrada local, para distinguir «sirvio el grafo» de «sirvio lo local»."""
    d = os.path.join(root, "docs", "knowledge", "adr")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "ADR-001-local.md"), "w", encoding="utf-8") as f:
        f.write("---\nid: ADR-001\ntitulo: Decision local sobre memoria\nestado: aceptada\n"
                "fecha: 2026-01-01\niniciativa: demo\n---\n\n# ADR-001\n\nmemoria local del proyecto\n")
    readme = os.path.join(root, "docs", "knowledge", "README.md")
    with open(readme, "w", encoding="utf-8") as f:
        f.write("| ADR-001 | Decision local sobre memoria | memoria | adr/ADR-001-local.md |\n")


def run(*args, cwd=None):
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    r = subprocess.run([sys.executable, SCRIPT, *args], cwd=cwd or ROOT, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return r.returncode, r.stdout, r.stderr


# --------------------------------------------------------------- reglas del router (config pura)

def test_backends_para_intent_solo_los_habilitados_que_declaran_el_intent():
    config = {"backends": {
        "a": {"type": "stub", "enabled": True, "config": {"router": {"intents": {"temporal": True}}}},
        "b": {"type": "stub", "enabled": False, "config": {"router": {"intents": {"temporal": True}}}},
        "c": {"type": "stub", "enabled": True, "config": {"router": {"intents": {"temporal": False}}}},
        "d": {"type": "stub", "enabled": True, "config": {"router": {"intents": {"relacional": True}}}},
    }}
    assert [b[0] for b in kf.backends_para_intent(config, "temporal")] == ["a"]
    assert [b[0] for b in kf.backends_para_intent(config, "relacional")] == ["d"]
    assert kf.backends_para_intent(config, "evidencia") == []


def test_backends_para_intent_exige_true_estricto_no_verdad_difusa():
    """`intents.temporal: "si"`/`1` NO declara el intent: la regla es un booleano `true`."""
    for valor in ("si", 1, "true", {}, [1]):
        config = {"backends": {"g": {"type": "stub", "enabled": True,
                                     "config": {"router": {"intents": {"temporal": valor}}}}}}
        assert kf.backends_para_intent(config, "temporal") == [], valor


def test_backends_para_intent_sin_backends_ni_router():
    assert kf.backends_para_intent({}, "temporal") == []
    assert kf.backends_para_intent({"backends": {"g": {"type": "stub", "enabled": True}}}, "temporal") == []


# --------------------------------------------------------------- las tres rutas de la Verificacion

def test_intent_declarado_y_mode_read_consulta_el_backend(tmp_path):
    root = str(tmp_path)
    _corpus_local(root)
    _taxonomia(root)
    stub = _escribir_stub(str(tmp_path / "bk"))
    aciertos, info = kf.consultar_intent(root, "temporal", texto="memoria", limit=5, directorios=[stub])
    assert info["origen"] == "backend"
    assert info["backend"] == "grafo"
    assert [a["id"] for a in aciertos] == ["ADR-100"]
    # el adaptador recibe la CONFIG declarada (no la inventa el router) y la consulta del usuario
    with open(os.path.join(stub, "llamadas.json"), encoding="utf-8") as f:
        llamada = json.load(f)
    assert llamada["cfg_group_id"] == "proyecto-demo"
    assert llamada["consulta"]["texto"] == "memoria"
    assert llamada["consulta"]["intent"] == "temporal"


def test_intent_no_declarado_cae_al_camino_local(tmp_path):
    root = str(tmp_path)
    _corpus_local(root)
    _taxonomia(root, intents={"temporal": True})
    stub = _escribir_stub(str(tmp_path / "bk"))
    aciertos, info = kf.consultar_intent(root, "relacional", texto="memoria", limit=5, directorios=[stub])
    assert info["origen"] == "local"
    assert aciertos is None          # el router NO resuelve la consulta local: la deja al camino de siempre
    assert "relacional" in info["motivo"]


def test_mode_shadow_no_lee_aunque_el_intent_este_declarado(tmp_path):
    """CA-10: en `shadow` se sincroniza pero NUNCA se lee — lo impone el `puede_leer` del adaptador."""
    root = str(tmp_path)
    _corpus_local(root)
    _taxonomia(root, mode="shadow")
    stub = _escribir_stub(str(tmp_path / "bk"),
                          puede={"puede": False, "razon": "mode='shadow' no autoriza lectura (solo `read`)"})
    aciertos, info = kf.consultar_intent(root, "temporal", texto="memoria", limit=5, directorios=[stub])
    assert aciertos is None
    assert info["origen"] == "local"
    assert "shadow" in info["motivo"]
    assert not os.path.exists(os.path.join(stub, "llamadas.json"))   # no se consulto el grafo


# --------------------------------------------------------------- degradaciones (nunca bloquean)

def test_backend_deshabilitado_no_enruta(tmp_path):
    root = str(tmp_path)
    _taxonomia(root, enabled=False)
    stub = _escribir_stub(str(tmp_path / "bk"))
    _aciertos, info = kf.consultar_intent(root, "temporal", texto="x", limit=5, directorios=[stub])
    assert info["origen"] == "local"


def test_adaptador_sin_funcion_de_consulta_degrada_a_local(tmp_path):
    root = str(tmp_path)
    _taxonomia(root)
    stub = _escribir_stub(str(tmp_path / "bk"), con_consulta=False)
    aciertos, info = kf.consultar_intent(root, "temporal", texto="x", limit=5, directorios=[stub])
    assert aciertos is None
    assert info["origen"] == "local"
    assert "consultar" in info["motivo"]


def test_adaptador_inexistente_degrada_a_local(tmp_path):
    root = str(tmp_path)
    _taxonomia(root, tipo="no-existe")
    aciertos, info = kf.consultar_intent(root, "temporal", texto="x", limit=5,
                                         directorios=[str(tmp_path / "vacio")])
    assert aciertos is None
    assert info["origen"] == "local"


def test_adaptador_que_lanza_degrada_a_local(tmp_path):
    root = str(tmp_path)
    _taxonomia(root)
    stub = _escribir_stub(str(tmp_path / "bk"))
    with open(os.path.join(stub, "stub.py"), "a", encoding="utf-8") as f:
        f.write("\ndef consultar(cfg, consulta):\n    raise RuntimeError('boom')\n")
    aciertos, info = kf.consultar_intent(root, "temporal", texto="x", limit=5, directorios=[stub])
    assert aciertos is None
    assert info["origen"] == "local"
    assert "boom" in info["motivo"]


def test_taxonomia_invalida_degrada_a_local_sin_lanzar(tmp_path):
    root = str(tmp_path)
    destino = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(destino, "taxonomy.json"), "w", encoding="utf-8") as f:
        f.write("{ no es json")
    aciertos, info = kf.consultar_intent(root, "temporal", texto="x", limit=5)
    assert aciertos is None
    assert info["origen"] == "local"


# --------------------------------------------------------------- forma de los aciertos remotos

def test_acierto_remoto_sin_evidencia_estado_o_ruta_se_descarta(tmp_path):
    """Fail-closed: un acierto que no trae evidencia, estado y ruta canonica no se sirve."""
    root = str(tmp_path)
    _taxonomia(root)
    incompletos = [
        dict(_ACIERTO_REMOTO, evidencia=""),
        dict(_ACIERTO_REMOTO, estado=None),
        {k: v for k, v in _ACIERTO_REMOTO.items() if k != "ruta"},
        dict(_ACIERTO_REMOTO, id=""),
    ]
    stub = _escribir_stub(str(tmp_path / "bk"), aciertos=incompletos)
    aciertos, info = kf.consultar_intent(root, "temporal", texto="x", limit=5, directorios=[stub])
    assert aciertos == []
    assert info["origen"] == "backend"
    assert info["descartados"] == 4


def test_acierto_remoto_trae_evidencia_estado_y_ruta_canonica_en_json(tmp_path):
    root = str(tmp_path)
    _taxonomia(root)
    stub = _escribir_stub(str(tmp_path / "bk"))
    aciertos, _info = kf.consultar_intent(root, "temporal", texto="x", limit=5, directorios=[stub])
    j = kf.acierto_json(aciertos[0])
    assert j["id"] == "ADR-100"
    assert j["estado"] == "aprobado"
    assert j["evidencia"] == "validated_case"
    assert j["ruta"] == "docs/knowledge/approved/adr/ADR-100-grafo.md"
    assert j["origen"] == "backend:grafo"
    assert "ADR-100" in j["linea"] and len(j["linea"]) <= kf.LINEA_MAX


def test_limit_se_respeta_en_los_aciertos_remotos(tmp_path):
    root = str(tmp_path)
    _taxonomia(root)
    muchos = [dict(_ACIERTO_REMOTO, id="ADR-1%02d" % i) for i in range(9)]
    stub = _escribir_stub(str(tmp_path / "bk"), aciertos=muchos)
    aciertos, _info = kf.consultar_intent(root, "temporal", texto="x", limit=3, directorios=[stub])
    assert len(aciertos) == 3


# --------------------------------------------------------------- CLI

def test_cli_intent_sirve_el_grafo_y_lo_declara_en_json(tmp_path):
    root = str(tmp_path)
    _corpus_local(root)
    _taxonomia(root)
    stub = _escribir_stub(str(tmp_path / "bk"))
    code, out, _err = run("memoria", "--intent", "temporal", "--json", "--root", root,
                          "--backends-dir", stub)
    assert code == 0
    data = json.loads(out)
    assert data["router"]["intent"] == "temporal"
    assert data["router"]["origen"] == "backend"
    assert data["router"]["backend"] == "grafo"
    assert [a["id"] for a in data["aciertos"]] == ["ADR-100"]
    assert data["aciertos"][0]["evidencia"] == "validated_case"


def test_cli_intent_no_declarado_sirve_lo_local(tmp_path):
    root = str(tmp_path)
    _corpus_local(root)
    _taxonomia(root, intents={"temporal": True})
    code, out, _err = run("memoria", "--intent", "evidencia", "--json", "--root", root)
    assert code == 0
    data = json.loads(out)
    assert data["router"]["origen"] == "local"
    assert data["consulta"]["intent"] == "evidencia"
    assert [a["id"] for a in data["aciertos"]] == ["ADR-001"]


def test_cli_sin_intent_no_toca_el_router_ni_cambia_el_contrato(tmp_path):
    root = str(tmp_path)
    _corpus_local(root)
    _taxonomia(root)
    code, out, _err = run("memoria", "--json", "--root", root)
    assert code == 0
    data = json.loads(out)
    assert "router" not in data and "intent" not in data["consulta"]
    assert [a["id"] for a in data["aciertos"]] == ["ADR-001"]


def test_cli_intent_con_show_o_related_es_error_de_uso(tmp_path):
    root = str(tmp_path)
    _corpus_local(root)
    code, _out, err = run("--intent", "temporal", "--show", "ADR-001", "--root", root)
    assert code == 2 and "intent" in err.lower()


def test_cli_intent_con_doctrina_es_error_de_uso():
    code, _out, err = run("x", "--intent", "temporal", "--doctrina")
    assert code == 2 and "intent" in err.lower()


def test_cli_intent_invalido_es_error_de_uso(tmp_path):
    code, _out, err = run("x", "--intent", "../../etc", "--root", str(tmp_path))
    assert code == 2 and "intent" in err.lower()


def test_cli_intent_degradado_avisa_por_stderr_y_sale_0(tmp_path):
    """Degradacion, no bloqueo: el grafo no sirve -> local, aviso en stderr, exit 0."""
    root = str(tmp_path)
    _corpus_local(root)
    _taxonomia(root, mode="shadow")
    stub = _escribir_stub(str(tmp_path / "bk"),
                          puede={"puede": False, "razon": "mode='shadow' no autoriza lectura"})
    code, out, err = run("memoria", "--intent", "temporal", "--json", "--root", root,
                         "--backends-dir", stub)
    assert code == 0
    assert "shadow" in err
    assert json.loads(out)["router"]["origen"] == "local"


def test_el_nucleo_no_nombra_ningun_backend_concreto():
    """Invariante del plan (`improvement-plan.md`): el nucleo no menciona el backend de grafo."""
    with open(SCRIPT, encoding="utf-8") as f:
        assert "graphiti" not in f.read().lower()
