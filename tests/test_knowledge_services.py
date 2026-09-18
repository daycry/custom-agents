"""Suite de REGRESIÓN END-TO-END de `knowledge-services` (ADR-018, T-10, cierre de la Fase 4).

No repite la cobertura unitaria ya existente de cada pieza (`agent-kits/shared/
test_knowledge_schema.py`, `test_knowledge_index_canonico.py`, `agent-kits/knowledge-curator/
test_curator_gate.py`, `skills/knowledge-services/scripts/test_knowledge_sync.py`,
`test_backend_markdown_export.py`, `agent-kits/shared/test_capabilities.py`): ejercita el flujo
COMPLETO encadenado — taxonomía → índice → curator-gate (approve/reject) → knowledge-sync
(dry-run/apply/check/rebuild/outbox-status) → doctor (bloque de capacidades) → export — sobre un
proyecto sintético en `tempfile`, con el backend `test` (fixture de `evals/fixtures/
knowledge-services/backend_test.py`) y, para los casos de red, `markdown-export` con un servidor
HTTP falso en `127.0.0.1`. Añade además los tres casos heredados de la revisión de dos lentes
(Fase 2 intento 2) que quedaron anotados para esta tarea: comentario/`#`/item vacío en una lista de
bloque del frontmatter, `min_evidence` no-string, coste de `realpath` — esos ya tienen su RED/GREEN
propio en `agent-kits/shared/test_knowledge_index_canonico.py` y `test_knowledge_schema.py`; aquí
solo se referencian para que quien lea esta suite sepa dónde viven.

Ejecutar: python -m pytest -q tests/test_knowledge_services.py
"""
import importlib.util
import json
import os
import sys
import threading

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, "agent-kits", "shared")
CURATOR_KIT = os.path.join(ROOT, "agent-kits", "knowledge-curator")
KS_SCRIPTS = os.path.join(ROOT, "skills", "knowledge-services", "scripts")
BACKENDS_DIR = os.path.join(ROOT, "skills", "knowledge-services", "backends")
FIXTURES_BACKENDS = os.path.join(ROOT, "evals", "fixtures", "knowledge-services")
HOOKS_DIR = os.path.join(ROOT, "hooks")


def _load(ruta, nombre_modulo):
    spec = importlib.util.spec_from_file_location(nombre_modulo, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre_modulo] = mod
    spec.loader.exec_module(mod)
    return mod


ks = _load(os.path.join(SHARED, "knowledge-schema.py"), "e2e_knowledge_schema")
ki = _load(os.path.join(SHARED, "knowledge-index.py"), "e2e_knowledge_index")
cg = _load(os.path.join(CURATOR_KIT, "curator-gate.py"), "e2e_curator_gate")
ks_sync = _load(os.path.join(KS_SCRIPTS, "knowledge-sync.py"), "e2e_knowledge_sync")
capabilities = _load(os.path.join(SHARED, "capabilities.py"), "e2e_capabilities")
markdown_export = _load(os.path.join(BACKENDS_DIR, "markdown_export.py"), "e2e_markdown_export")


# ------------------------------------------------------------------ helpers ----

def _taxonomy(root, categories, backends=None, denylist=None):
    if backends is None:
        # Las categorías de `_categorias_base()` citan `testx` en su `routing`; sin esta entrada
        # `validar()` lo rechaza en fail-closed («routing cita un backend no declarado») y
        # `build_index` corta ANTES de escanear ningún fichero — no es el fallo que cada test
        # concreto quiere ejercitar, así que el default lo declara (deshabilitado) salvo que el
        # test pase su propio `backends`.
        backends = {"testx": {"type": "test", "enabled": False, "config": {}}}
    cfg = {
        "version": 1,
        "id_prefix": "ks",
        "categories": categories,
        "evidence_levels": ["observation", "single_case", "validated_case",
                             "multiple_validated_cases", "human_confirmed_rule"],
        "backends": backends,
    }
    if denylist:
        cfg["denylist"] = denylist
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return cfg


def _candidato(root, id_, category, evidencia="observation", carpeta="pending", cuerpo="Cuerpo real."):
    d = os.path.join(root, "docs", "knowledge", "candidates", carpeta)
    os.makedirs(d, exist_ok=True)
    ruta = os.path.join(d, f"{id_}.md")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(
            f"---\nid: {id_}\nversion: 1\ncategory: {category}\nevidencia: {evidencia}\n"
            f"fuentes:\n  - https://x\ntags:\n  - clave:valor\n---\n\n{cuerpo}\n"
        )
    return ruta


def _aprobar_en_disco(root, ruta_candidato, folder, id_, category):
    """Simula el paso P4 del `knowledge-curator` (no lo hace `curator-gate.py`, que solo dictamina):
    mueve el candidato a `approved/<folder>/` con `estado: aprobado` añadido."""
    with open(ruta_candidato, encoding="utf-8") as f:
        texto = f.read()
    texto = texto.replace(f"category: {category}\n", f"category: {category}\nestado: aprobado\n", 1)
    destino_dir = os.path.join(root, "docs", "knowledge", "approved", folder)
    os.makedirs(destino_dir, exist_ok=True)
    destino = os.path.join(destino_dir, f"{id_}.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(texto)
    os.remove(ruta_candidato)
    return destino


def _categorias_base():
    return [
        {"key": "ENRUTADA", "folder": "gotchas", "min_evidence": "observation",
         "routing": {"testx": True}},
        {"key": "SIN_ROUTING", "folder": "gotchas", "min_evidence": "observation"},
        {"key": "DESACTIVADA", "folder": "adr", "min_evidence": "observation",
         "routing": {"testx": False}},
    ]


# ------------------------------------------------------------------ E2E feliz ----

def test_flujo_completo_taxonomia_indice_curator_sync_doctor_backend_test(tmp_path, capsys):
    """Flujo íntegro con el backend `test` de fixture: aprobar dos candidatos (uno enrutado, uno
    sin routing), rechazar uno tercero, indexar, publicar (apply real con outbox), --check,
    --rebuild y --outbox-status, y comprobar que `/doctor` (bloque de capacidades) ve el backend
    activo a través de `capabilities.py`."""
    root = str(tmp_path)
    _taxonomy(root, _categorias_base(),
              backends={"testx": {"type": "test", "enabled": True, "config": {}}})

    c1 = _candidato(root, "e1", "ENRUTADA")
    c2 = _candidato(root, "e2", "SIN_ROUTING")
    c3 = _candidato(root, "e3-rechazado", "ENRUTADA")

    veredicto1, exit1 = cg.evaluar(c1, "approve", root=root)
    assert exit1 == 0, veredicto1
    veredicto2, exit2 = cg.evaluar(c2, "approve", root=root)
    assert exit2 == 0, veredicto2
    veredicto3, exit3 = cg.evaluar(c3, "reject", root=root)
    assert exit3 == 0, veredicto3

    _aprobar_en_disco(root, c1, "gotchas", "e1", "ENRUTADA")
    _aprobar_en_disco(root, c2, "gotchas", "e2", "SIN_ROUTING")
    # e3 rechazado: NO se mueve a approved/, sigue en candidates/pending/ (o donde lo deje el
    # curador) — nunca debe aparecer en el índice ni en la publicación.

    indice, errores_indice = ki.build_index(root)
    assert errores_indice == []
    assert set(indice) == {"e1", "e2"}

    # --dry-run: solo e1 (ENRUTADA) llega al plan; e2 (SIN_ROUTING) se omite por routing.
    assert ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--dry-run", "--json"]) == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["entradas"] == 1
    assert salida["ops"][0]["id"] == "e1"

    # Publicación real (apply + outbox).
    assert ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS]) == 0
    capsys.readouterr()

    # --check: health/verify del backend fixture, sano por defecto.
    assert ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--check", "--json"]) == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["health"]["estado"] == "sano"
    assert salida["verify"]["ok"] is True

    # --rebuild: reconstruye sobre TODAS las entradas ya enrutadas (solo e1).
    assert ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--rebuild", "--json"]) == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["rebuild"]["reconstruidos"] == 1

    # --outbox-status: la cola de este backend, sin publicar nada nuevo.
    assert ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--outbox-status", "--json"]) == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["backend"] == "testx"

    # `/doctor` ve el backend a través de `capabilities.py` (E17): el registro base siempre
    # declara `knowledge-gate`, y con taxonomy de proyecto su `enabled` refleja que hay categorías
    # con routing configurado (no revienta, no hace falta red real).
    resultado = capabilities.enumerar(root=root)
    kg = next(c for c in resultado if c["id"] == "knowledge-gate")
    assert kg["enabled"] is True


# ------------------------------------------------------------------ mutantes de filtrado mueren ----

def test_mutante_routing_false_nunca_llega_al_adaptador(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias_base(),
              backends={"testx": {"type": "test", "enabled": True, "config": {}}})
    c = _candidato(root, "desactivada-1", "DESACTIVADA")
    veredicto, exit_ = cg.evaluar(c, "approve", root=root)
    assert exit_ == 0, veredicto
    _aprobar_en_disco(root, c, "adr", "desactivada-1", "DESACTIVADA")

    assert ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--dry-run", "--json"]) == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["entradas"] == 0
    assert salida["ops"] == []


def test_mutante_categoria_sin_routing_declarado_nunca_exporta(tmp_path, capsys):
    root = str(tmp_path)
    _taxonomy(root, _categorias_base(),
              backends={"testx": {"type": "test", "enabled": True, "config": {}}})
    c = _candidato(root, "sin-routing-1", "SIN_ROUTING")
    veredicto, exit_ = cg.evaluar(c, "approve", root=root)
    assert exit_ == 0, veredicto
    _aprobar_en_disco(root, c, "gotchas", "sin-routing-1", "SIN_ROUTING")

    assert ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--dry-run", "--json"]) == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["entradas"] == 0


def test_mutante_candidato_en_candidates_nunca_se_indexa_ni_exporta(tmp_path, capsys):
    """Un candidato jamás movido a `approved/` (aprobado o no) no puede llegar al índice ni al
    adaptador — `knowledge-index.py` NUNCA escanea `docs/knowledge/candidates/**`."""
    root = str(tmp_path)
    _taxonomy(root, _categorias_base(),
              backends={"testx": {"type": "test", "enabled": True, "config": {}}})
    _candidato(root, "nunca-aprobado", "ENRUTADA")

    indice, errores = ki.build_index(root)
    assert errores == []
    assert "nunca-aprobado" not in indice

    assert ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--dry-run", "--json"]) == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["entradas"] == 0


def test_mutante_denylist_bloquea_la_aprobacion(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _categorias_base(),
              backends={"testx": {"type": "test", "enabled": True, "config": {}}},
              denylist=["informacion sensible"])
    c = _candidato(root, "con-denylist", "ENRUTADA", cuerpo="Esto contiene informacion sensible del cliente.")
    veredicto, exit_ = cg.evaluar(c, "approve", root=root)
    assert exit_ == 1
    assert any(e["campo"] == "denylist" for e in veredicto["errores"]), veredicto


# ------------------------------------------------------------------ YAML/JSON corrupto ----

def _escribir_taxonomy_cruda(root, contenido_bytes):
    d = os.path.join(root, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "wb") as f:
        f.write(contenido_bytes)


def test_taxonomy_json_corrupto_falla_de_forma_segura(tmp_path, capsys):
    root = str(tmp_path)
    _escribir_taxonomy_cruda(root, b"{esto no es json")
    exit_ = ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--dry-run"])
    assert exit_ == 2
    err = capsys.readouterr().err
    assert "JSON ilegible" in err
    assert "Traceback" not in err


def test_taxonomy_json_con_bom_utf8_se_tolera(tmp_path):
    root = str(tmp_path)
    cfg = {"version": 1, "id_prefix": "ks", "categories": _categorias_base(),
           "evidence_levels": ["observation"],
           "backends": {"testx": {"type": "test", "enabled": False, "config": {}}}}
    _escribir_taxonomy_cruda(root, b"\xef\xbb\xbf" + json.dumps(cfg).encode("utf-8"))
    config, origen, _ruta, errores = ks.cargar_taxonomia(root)
    assert origen == "proyecto"
    assert config is not None
    assert errores == []


def test_taxonomy_json_utf16_falla_de_forma_segura_sin_traceback(tmp_path, capsys):
    root = str(tmp_path)
    cfg = {"version": 1, "id_prefix": "ks", "categories": _categorias_base(),
           "evidence_levels": ["observation"],
           "backends": {"testx": {"type": "test", "enabled": False, "config": {}}}}
    _escribir_taxonomy_cruda(root, json.dumps(cfg).encode("utf-16"))
    exit_ = ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--dry-run"])
    assert exit_ == 2
    err = capsys.readouterr().err
    assert "Traceback" not in err


# ------------------------------------------------------------------ rutas maliciosas ----

def test_folder_con_escape_se_rechaza_en_la_taxonomia():
    cfg = json.loads(json.dumps(ks._TAXONOMY_FALLBACK))
    cfg["categories"] = [{"key": "X", "folder": "../candidates/pending",
                           "min_evidence": "observation", "routing": {}}]
    errores = ks.validar(cfg, "t")
    assert any(e["campo"] == "categories[0].folder" for e in errores)


def test_id_con_escape_no_se_indexa_y_no_escribe_nada(tmp_path):
    root = str(tmp_path)
    _taxonomy(root, _categorias_base())
    d = os.path.join(root, "docs", "knowledge", "approved", "gotchas")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "escape.md"), "w", encoding="utf-8") as f:
        f.write("---\nid: ../../ESCAPE\nversion: 1\nestado: aprobado\ncategory: ENRUTADA\n---\n\nx\n")
    indice, errores = ki.build_index(root)
    assert indice == {}
    assert any(e["campo"] == "id" for e in errores)


def test_type_con_escape_se_rechaza_antes_de_tocar_disco():
    with pytest.raises(Exception) as exc_info:
        sys.path.insert(0, BACKENDS_DIR)
        try:
            binit = _load(os.path.join(BACKENDS_DIR, "__init__.py"), "e2e_backends_init")
            binit.cargar_adaptador("../../etc/passwd", directorios=[BACKENDS_DIR])
        finally:
            sys.path.remove(BACKENDS_DIR)
    assert "no cumple la forma" in str(exc_info.value)


def test_export_dir_dentro_de_docs_knowledge_se_rechaza(tmp_path):
    root = str(tmp_path)
    cfg = {"_root": root, "export_dir": os.path.join("docs", "knowledge", "approved", "export")}
    with pytest.raises(markdown_export.ConfigInvalida):
        markdown_export._export_dir_resuelto(cfg)


def test_export_dir_ancestro_del_root_se_rechaza(tmp_path):
    root = os.path.join(str(tmp_path), "proyecto", "anidado")
    os.makedirs(root, exist_ok=True)
    cfg = {"_root": root, "export_dir": ".."}
    with pytest.raises(markdown_export.ConfigInvalida):
        markdown_export._export_dir_resuelto(cfg)


def test_health_url_file_scheme_se_rechaza_sin_abrir_nada():
    salud = markdown_export.health({"health": {"url": "file:///etc/passwd", "timeout_ms": 100}})
    assert salud["estado"] == "error"


def test_health_url_host_publico_se_rechaza_sin_conexion():
    salud = markdown_export.health({"health": {"url": "http://example.com/health", "timeout_ms": 100}})
    assert salud["estado"] == "error"
    assert "no local" in salud["detalle"]


def test_health_url_redireccion_a_host_publico_se_rechaza(tmp_path):
    """Un servidor local (permitido) que redirige a un host público no debe seguir la
    redirección — mismo criterio SSRF que un `health.url` público directo."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", "http://example.com/health")
            self.end_headers()

        def log_message(self, *a, **k):  # noqa: D401 - silenciar logging de test
            pass

    httpd = HTTPServer(("127.0.0.1", 0), _Handler)
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    try:
        puerto = httpd.server_address[1]
        salud = markdown_export.health(
            {"health": {"url": f"http://127.0.0.1:{puerto}/health", "timeout_ms": 500}})
        assert salud["estado"] == "error"
        assert "redirecci" in salud["detalle"]
    finally:
        httpd.shutdown()
        hilo.join(timeout=2)


# ------------------------------------------------------------------ hooks sin red ----

def test_ningun_hook_invoca_knowledge_sync_ni_curator_gate():
    """CA de la spec «red desde hooks» fuera de alcance: ningún hook del ciclo (`hooks/*.sh`,
    `hooks/hooks.json`) debe disparar `knowledge-sync.py` ni `curator-gate.py` — ambos hacen red
    (el backend `markdown-export`) o mutan `docs/knowledge/`, y los hooks del ciclo (PostToolUse,
    SubagentStop, SessionStart/End, UserPromptSubmit) SOLO informan (systemMessage/
    additionalContext), nunca ejecutan lógica de publicación."""
    prohibido = ("knowledge-sync.py", "curator-gate.py")
    ofensores = []
    for nombre in sorted(os.listdir(HOOKS_DIR)):
        ruta = os.path.join(HOOKS_DIR, nombre)
        if not os.path.isfile(ruta):
            continue
        try:
            with open(ruta, encoding="utf-8") as f:
                texto = f.read()
        except UnicodeDecodeError:
            continue
        for termino in prohibido:
            if termino in texto:
                ofensores.append((nombre, termino))
    assert ofensores == [], f"hook invoca un script de red/mutación de docs/knowledge: {ofensores}"
