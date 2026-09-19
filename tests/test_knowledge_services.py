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
import re
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
    adaptador — `knowledge-index.py` NUNCA escanea `docs/knowledge/candidates/**`.

    Gap 160 (revisión de dos lentes, Fase 4 intento 1): la versión anterior afirmaba el negativo
    sobre un universo VACÍO — `approved/` no tenía ninguna entrada, así que "el candidato no está
    en el índice" era trivialmente cierto (el índice estaba vacío por completo, no porque hubiera
    filtrado nada). La versión fuerte crea TAMBIÉN una entrada válida en `approved/<folder>` y
    comprueba que el índice contiene ESA entrada (el escaneo funciona) y no el candidato (el
    filtro funciona) — un mutante que hiciera `build_index` escanear `candidates/**` entero haría
    fallar esta aserción del recuento, cosa que la versión vacía anterior nunca podía detectar."""
    root = str(tmp_path)
    _taxonomy(root, _categorias_base(),
              backends={"testx": {"type": "test", "enabled": True, "config": {}}})
    _candidato(root, "nunca-aprobado", "ENRUTADA")
    ruta_aprobada = _candidato(root, "si-aprobada", "ENRUTADA", carpeta="pending")
    _aprobar_en_disco(root, ruta_aprobada, "gotchas", "si-aprobada", "ENRUTADA")

    indice, errores = ki.build_index(root)
    assert errores == []
    assert "nunca-aprobado" not in indice
    assert set(indice) == {"si-aprobada"}

    assert ks_sync.main(["--backend", "testx", "--root", root, "--backends-dir", FIXTURES_BACKENDS, "--dry-run", "--json"]) == 0
    salida = json.loads(capsys.readouterr().out)
    assert salida["entradas"] == 1


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


def test_host_permitido_rechaza_scheme_file_con_host_local_declarado():
    """Gap 142 (revisión de dos lentes, Fase 4 intento 1): el test anterior (`file:///etc/passwd`)
    es vacuo — esa URL no tiene host (`urlsplit(...).hostname` es `None`), así que cae por «sin
    host», no por el allowlist de esquemas: un mutante que añadiera `file` al allowlist
    (`("http", "https", "file")`) seguiría pasando ese test sin que nadie lo notara. Con un host
    LOCAL explícito (`file://localhost/x.json`) la única cosa que puede rechazar la URL es el
    chequeo de esquema — si el mutante lo quitara, esto pasaría a `True`."""
    assert markdown_export._host_permitido("file://localhost/x.json") is False
    assert markdown_export._host_permitido("http://127.0.0.1/x") is True


def test_health_url_file_scheme_con_host_local_se_rechaza_sin_resolver_dns(monkeypatch):
    """Complementa el test anterior verificando además el efecto observable en `health()`: se
    rechaza sin abrir ninguna conexión ni resolver DNS (espía sobre `socket.gethostbyname`)."""
    llamadas = []
    monkeypatch.setattr(
        markdown_export.socket, "gethostbyname",
        lambda h: llamadas.append(h) or (_ for _ in ()).throw(OSError("no debería llamarse")))
    salud = markdown_export.health(
        {"health": {"url": "file://localhost/x.json", "timeout_ms": 100}})
    assert salud["estado"] == "error"
    assert llamadas == []


# gap 175 (revisión de dos lentes, Fase 4 intento 2): el test anterior de host público usaba
# `example.com`, que hace una resolución DNS REAL en cada corrida de la suite (lenta, no
# determinista sin red, y un host genuino de terceros al que no deberíamos apuntar ni para
# resolverlo). Se retira en favor del siguiente, que cubre EXACTAMENTE el mismo caso (host
# público rechazado, `estado == "error"`, `"no local"` en el detalle) con una IP literal y un
# espía sobre `socket.gethostbyname` que demuestra que no hace ninguna llamada — ningún test de
# esta suite hace ya DNS real.
def test_health_url_host_publico_ip_literal_se_rechaza_sin_dns_real(monkeypatch):
    """Gap 152: la versión con `example.com` hace una resolución DNS REAL (lenta y no
    determinista en CI sin red); usando una IP pública LITERAL no hace falta resolver nada — el
    rechazo se decide con `ipaddress.ip_address` puro, sin tocar la red — y sigue siendo un host
    no local/privado genuino (no un accidente de "no hay DNS", que sería el motivo equivocado)."""
    llamadas = []
    monkeypatch.setattr(markdown_export.socket, "gethostbyname",
                         lambda h: llamadas.append(h) or "0.0.0.0")
    salud = markdown_export.health(
        {"health": {"url": "http://93.184.216.34/health", "timeout_ms": 100}})
    assert salud["estado"] == "error"
    assert "no local" in salud["detalle"]
    assert llamadas == []  # una IP literal no necesita resolución DNS


def test_health_url_redireccion_a_host_publico_se_rechaza(tmp_path, monkeypatch):
    """Un servidor local (permitido) que redirige a un host público no debe seguir la
    redirección — mismo criterio SSRF que un `health.url` público directo.

    Gap 179 (revisión Fase 4 intento 3): la versión anterior redirigía a `http://example.com/
    health`, que hace una resolución DNS REAL (la evidencia del gap 175 — «ningún test de esta
    suite hace ya DNS real» — era falsa mientras este test siguiera vivo). Se usa la misma IP
    pública LITERAL que el gap 152 (`93.184.216.34`; `203.0.113.1`/TEST-NET-3 NO sirve aquí porque
    `ipaddress.ip_address(...).is_private` la clasifica como privada/reservada en la stdlib, así
    que `_host_permitido` la aceptaría y el test intentaría conectar de verdad) y un espía sobre
    `socket.gethostbyname` que falla si se le llama con un hostname (no una IP) — así queda
    demostrado que NINGÚN salto de esta cadena de redirección resuelve DNS de verdad."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    llamadas = []

    def _gethostbyname_espia(host):
        llamadas.append(host)
        raise AssertionError(f"DNS real para {host!r}: gap 179, no debería resolverse nada")

    monkeypatch.setattr(markdown_export.socket, "gethostbyname", _gethostbyname_espia)

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", "http://93.184.216.34/health")
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
        assert llamadas == [], f"hizo DNS real: {llamadas} (gap 179)"
    finally:
        httpd.shutdown()
        httpd.server_close()  # gap 153: sin esto el socket queda en TIME_WAIT/abierto
        hilo.join(timeout=2)
        assert not hilo.is_alive(), "el hilo del servidor de test no terminó (gap 153)"


def test_health_url_redireccion_a_location_mal_formado_no_lanza(tmp_path):
    """Gap 184 (revisión Fase 4 intento 3): un `Location` con un corchete de IPv6 sin cerrar
    (`http://[`) hace que `urllib.parse.urljoin`, dentro de `_urlopen_local`, lance `ValueError` —
    antes escapaba de `health()` sin capturar (pese a que su docstring promete «nunca lanza»);
    `verify()` ya lo capturaba porque su bloque agrupa `ValueError` por otra razón (el `json.loads`
    del snapshot). `health()` debe degradar igual que las demás ramas de red, no lanzar."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(302)
            self.send_header("Location", "http://[")
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
        assert "mal formad" in salud["detalle"]
    finally:
        httpd.shutdown()
        httpd.server_close()
        hilo.join(timeout=2)


def test_health_url_servidor_local_responde_no_http_no_lanza(tmp_path):
    """Gap 155: `health()` documenta «nunca lanza» pero dejaba escapar `http.client.HTTPException`
    (un servidor local que responde texto que no es una respuesta HTTP válida — `BadStatusLine`,
    subclase de `HTTPException`, no de `OSError`) hasta el llamador, que solo captura
    `Exception` genérico en algunos sitios. Un servidor local (permitido por el allowlist de host)
    que devuelve basura no-HTTP debe degradar a `estado: "error"`, nunca lanzar."""
    import socket as socket_mod

    servidor = socket_mod.socket(socket_mod.AF_INET, socket_mod.SOCK_STREAM)
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(1)
    puerto = servidor.getsockname()[1]

    def _responder():
        try:
            conn, _addr = servidor.accept()
            with conn:
                conn.recv(1024)
                conn.sendall(b"esto no es HTTP en absoluto\r\n\r\n")
        except OSError:
            pass

    hilo = threading.Thread(target=_responder, daemon=True)
    hilo.start()
    try:
        salud = markdown_export.health(
            {"health": {"url": f"http://127.0.0.1:{puerto}/health", "timeout_ms": 500}})
        assert salud["estado"] == "error"
    finally:
        servidor.close()
        hilo.join(timeout=2)
        assert not hilo.is_alive()


def test_verify_url_servidor_local_responde_no_http_no_lanza(tmp_path):
    """Gap 174: `health()` ya tenía cubierta la mitad de la excepción de `http.client.HTTPException`
    (gap 155), pero `verify()` captura la MISMA excepción en su propia llamada a `/graph/snapshot`
    (`markdown_export.py`) sin que ningún test la ejerciera — un mutante que quitara
    `http.client.HTTPException` de la tupla de `except` de `verify()` seguía dejando la suite en
    verde. Un servidor local (permitido) que responde texto no-HTTP debe degradar `verify()` a
    `ok: False`, nunca lanzar."""
    import socket as socket_mod

    export_dir = str(tmp_path / "export")
    os.makedirs(export_dir, exist_ok=True)
    manifest_path = os.path.join(export_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "entries": {
            "mr.pattern.x": {"ruta_relativa": "x.md", "hash": "abc"}}}, f)

    servidor = socket_mod.socket(socket_mod.AF_INET, socket_mod.SOCK_STREAM)
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(1)
    puerto = servidor.getsockname()[1]

    def _responder():
        try:
            conn, _addr = servidor.accept()
            with conn:
                conn.recv(1024)
                conn.sendall(b"esto no es HTTP en absoluto\r\n\r\n")
        except OSError:
            pass

    hilo = threading.Thread(target=_responder, daemon=True)
    hilo.start()
    try:
        cfg = {"export_dir": export_dir,
               "health": {"url": f"http://127.0.0.1:{puerto}/health", "timeout_ms": 500}}
        resultado = markdown_export.verify(cfg)
        assert resultado["ok"] is False
        assert resultado["desfase"]
    finally:
        servidor.close()
        hilo.join(timeout=2)
        assert not hilo.is_alive()


def test_health_y_verify_sanean_bytes_crudos_del_servidor_en_detalle_y_motivo(tmp_path):
    """Gap 176 (CWE-117, señalado fuera de lente por la Lente B): `health()`/`verify()` embebían
    los bytes crudos de la excepción de red (mensaje de `OSError`/`HTTPException`, que puede
    contener lo que el servidor haya devuelto) directamente en `detalle`/`motivo`, que acaban
    impresos por `/doctor` — un servidor que responda CRLF + secuencias ANSI podía inyectar
    saltos de línea/color en esa salida. Se sanea: recorte a 200 caracteres y los caracteres de
    control (incluidas secuencias ANSI) se sustituyen por un espacio."""
    import socket as socket_mod

    export_dir = str(tmp_path / "export")
    os.makedirs(export_dir, exist_ok=True)
    manifest_path = os.path.join(export_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "entries": {
            "mr.pattern.x": {"ruta_relativa": "x.md", "hash": "abc"}}}, f)

    def _servidor_con_basura_ansi():
        servidor = socket_mod.socket(socket_mod.AF_INET, socket_mod.SOCK_STREAM)
        servidor.bind(("127.0.0.1", 0))
        servidor.listen(1)
        puerto = servidor.getsockname()[1]

        def _responder():
            try:
                conn, _addr = servidor.accept()
                with conn:
                    conn.recv(1024)
                    conn.sendall(b"basura\r\n\x1b[31mrojo\x1b[0m\r\n\r\n")
            except OSError:
                pass

        hilo = threading.Thread(target=_responder, daemon=True)
        hilo.start()
        return servidor, hilo, puerto

    servidor, hilo, puerto = _servidor_con_basura_ansi()
    try:
        salud = markdown_export.health(
            {"health": {"url": f"http://127.0.0.1:{puerto}/health", "timeout_ms": 500}})
        assert salud["estado"] == "error"
        assert "\r" not in salud["detalle"]
        assert "\n" not in salud["detalle"]
        assert "\x1b" not in salud["detalle"]
        # gap 182 (revisión Fase 4 intento 3): la alternativa ANSI del patrón era INALCANZABLE
        # (`[ -]` de `[\x00-\x1f\x7f]` casaba antes que `\x1b\[[0-9;]*[A-Za-z]` al ser la primera
        # del `|`) — solo se sustituía el propio `\x1b`, dejando el resto de la secuencia
        # (`[31m`, `[0m`) intacto en el texto. La aserción anterior (`"\x1b" not in ...`) no lo
        # detectaba porque solo mira el ESC, no la secuencia completa.
        assert "[31m" not in salud["detalle"], salud["detalle"]
        assert "[0m" not in salud["detalle"], salud["detalle"]
        assert len(salud["detalle"]) <= 200
    finally:
        servidor.close()
        hilo.join(timeout=2)
        assert not hilo.is_alive()

    servidor, hilo, puerto = _servidor_con_basura_ansi()
    try:
        cfg = {"export_dir": export_dir,
               "health": {"url": f"http://127.0.0.1:{puerto}/health", "timeout_ms": 500}}
        resultado = markdown_export.verify(cfg)
        assert resultado["ok"] is False
        motivo = resultado["desfase"][0]["motivo"]
        assert "\r" not in motivo
        assert "\n" not in motivo
        assert "\x1b" not in motivo
        assert "[31m" not in motivo, motivo  # gap 182
        assert "[0m" not in motivo, motivo  # gap 182
        assert len(motivo) <= 200
    finally:
        servidor.close()
        hilo.join(timeout=2)
        assert not hilo.is_alive()


def test_gap182_tope_200_se_aplica_al_texto_del_servidor_no_al_prefijo(tmp_path):
    """Gap 182 (revisión Fase 4 intento 3): el tope de 200 caracteres se aplicaba DESPUÉS de
    anteponer el prefijo propio (`f"respuesta no HTTP de {url}: ..."` pasaba ENTERO por
    `_sanear_detalle`), así que una respuesta larga del servidor se llevaba menos de 200
    caracteres de margen (el prefijo se comía parte del tope) y además el prefijo podía
    desaparecer si el texto del servidor por sí solo ya llegaba a 200. El tope debe aplicarse
    SOLO al texto no confiable del servidor, con el prefijo (de confianza, generado por este
    módulo) SIEMPRE visible completo delante."""
    import socket as socket_mod

    servidor = socket_mod.socket(socket_mod.AF_INET, socket_mod.SOCK_STREAM)
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(1)
    puerto = servidor.getsockname()[1]
    basura = b"X" * 5000

    def _responder():
        try:
            conn, _addr = servidor.accept()
            with conn:
                conn.recv(1024)
                conn.sendall(basura + b"\r\n\r\n")
        except OSError:
            pass

    hilo = threading.Thread(target=_responder, daemon=True)
    hilo.start()
    try:
        salud = markdown_export.health(
            {"health": {"url": f"http://127.0.0.1:{puerto}/health", "timeout_ms": 500}})
        assert salud["estado"] == "error"
        assert salud["detalle"].startswith("respuesta no HTTP de "), salud["detalle"]
        assert "X" * 200 in salud["detalle"], salud["detalle"]
    finally:
        servidor.close()
        hilo.join(timeout=2)
        assert not hilo.is_alive()


# ------------------------------------------------------------------ hooks sin red ----

# gap 141/154 (revisión de dos lentes, Fase 4 intento 1): la lista anterior solo buscaba los dos
# nombres de script (`knowledge-sync.py`/`curator-gate.py`) en los ficheros DIRECTOS de `hooks/`
# (sin recursión), tragaba `UnicodeDecodeError` con un `continue` silencioso (un hook binario o
# corrupto quedaba sin analizar, no como fallo), y no miraba el frontmatter `hooks:` de
# `agents/*.md` (un agente puede declarar un hook `command` inline con la misma red prohibida sin
# que exista ningún fichero bajo `hooks/`). Se amplía a los términos de red/publicación que la
# revisión señaló (`urllib`, `urlopen`, `socket`, `http.client`, `requests`, `curl`, `wget`,
# `Invoke-WebRequest`, `markdown_export`) y a `knowledge-sync`/`curator-gate` SIN extensión (un
# `command` puede invocar el script por su nombre de módulo, sin `.py`, según el shell — gap 171,
# revisión Fase 4 intento 2: la lista anterior tenía `knowledge-sync` sin extensión pero no su
# gemelo `curator-gate`, asimetría sin motivo).
_TERMINOS_RED_PROHIBIDOS = (
    "knowledge-sync.py", "knowledge-sync", "curator-gate.py", "curator-gate", "markdown_export",
    "urllib", "urlopen", "socket", "http.client", "requests", "curl", "wget",
    "invoke-webrequest",
)

# gap 169 (revisión Fase 4 intento 2): comprobado con grep ANTES de este fix — ninguno de los
# scripts que los hooks/frontmatter invocan hoy (`agent-kits/shared/{guardrail-check,ledger-lint,
# progress-report,journal,skill-index,knowledge-find}.py`) usa `socket`/`urllib`/`http.client`/
# `requests`/`curl`/`wget` para nada, legítimo o no. Si alguno lo necesitase en el futuro (p. ej.
# una resolución DNS puramente local), se declara aquí con su ruta relativa al repo y el motivo —
# ese script queda excluido del escaneo de scripts invocados, nunca de los hooks/frontmatter
# directos.
_ALLOWLIST_USOS_LOCALES_DE_RED = frozenset()

_RUTA_SCRIPT_RE = re.compile(r"[\w./-]+\.(?:py|sh)")

# gap 181 (revisión Fase 4 intento 3): el seguimiento de invocaciones era de UN SOLO NIVEL
# (`session-journal.sh -> journal.py`, pero NO seguía lo que `journal.py` a su vez invoca —
# `outbox.py`). Se acota a 4 saltos para no perseguir una cola arbitrariamente larga; `vistos`
# corta cualquier ciclo real de invocaciones antes de llegar a ese tope.
_MAX_PROFUNDIDAD_SEGUIMIENTO = 4


def _texto_o_fallo_si_no_decodifica(ruta):
    """Lee un fichero en UTF-8; no decodificar es un FALLO explícito (gap 154), nunca un `skip`
    silencioso — un hook binario/corrupto que ADEMÁS invoque red no debe colarse por un
    `except: continue`."""
    with open(ruta, "rb") as f:
        crudo = f.read()
    try:
        return crudo.decode("utf-8")
    except UnicodeDecodeError as e:
        raise AssertionError(f"`{ruta}` no es UTF-8 decodificable: {e}") from e


def _lineas_de_codigo(texto, nombre_fichero=""):
    """Parte de CÓDIGO de cada línea (lo que precede al marcador de comentario) — gap 170: nada
    de subcadena sobre texto de comentario/documentación, ni para detectar un término prohibido
    (abajo) ni para seguir una invocación de script (gap 169: una línea que solo MENCIONE
    `outbox.py` en un comentario, sin invocarlo, no debe hacer que el escaneo lo siga).

    Gap 178 (revisión Fase 4 intento 3, REGRESIÓN del fix del gap 170): `linea.split(marcador,
    1)[0]` corta en el PRIMER marcador de la línea sin mirar si está dentro de una cadena
    entrecomillada — `sed "s/#.*//" x; curl …` cortaba en el `#` DENTRO de `"s/#.*//"` y perdía el
    `curl` que venía después (`1 passed` en vez de `1 failed`); en un `.js`, la `//` de una URL
    (`"https://evil"`) cortaba igual y escondía cualquier término posterior en la misma línea. Se
    recorta con `_recortar_comentario_de_codigo`, que respeta comillas simples/dobles y, para
    `//`, exige que no vaya precedido de `:` (para no tropezar con URLs sueltas fuera de
    comillas).

    Gap 181 (revisión Fase 4 intento 3, hallado al implementar el seguimiento transitivo): en
    `.py`, un DOCSTRING triple-comillado (`\"\"\"...\"\"\"`/`'''...'''`) es documentación, no
    código — este propio repositorio narra sus gaps en docstrings extensos que mencionan de
    pasada rutas de OTROS scripts reales (`evals/run.py`, `task-brief.py`, …), y con el
    seguimiento transitivo esas menciones se colaban como «invocaciones» y arrastraban ficheros
    ajenos (incluido, en una corrida real, `tests/test_console_encoding.py`) al escaneo de
    términos prohibidos. Se descartan ANTES de partir en líneas, igual que ya se descartan los
    comentarios `#`/`//`."""
    texto = _quitar_docstrings_triple_comilla(texto, nombre_fichero)
    marcador = "//" if nombre_fichero.endswith(".js") else "#"
    return [_recortar_comentario_de_codigo(linea, marcador) for linea in texto.splitlines()]


_DOCSTRING_TRIPLE_RE = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'')


def _quitar_docstrings_triple_comilla(texto, nombre_fichero):
    """Gap 181: solo se aplica a `.py` — un docstring triple-comillado es EXCLUSIVO de Python; en
    `.sh`/`.js` no existe esa sintaxis y `'''`/`\"\"\"` ahí serían, como mucho, tres comillas
    simples seguidas (ya cubiertas por el recorte por comillas de `_recortar_comentario_de_codigo`
    línea a línea)."""
    if not nombre_fichero.endswith(".py"):
        return texto
    return _DOCSTRING_TRIPLE_RE.sub("", texto)


def _recortar_comentario_de_codigo(linea, marcador):
    """Recorta `linea` en la primera aparición REAL del `marcador` de comentario: fuera de
    cualquier cadena entrecomillada (`'`/`"`) y, si el marcador es `//`, solo si no va precedido
    de `:` (para no tropezar con `https://…` cuando aparece fuera de comillas)."""
    comilla_abierta = None
    m = len(marcador)
    i = 0
    n = len(linea)
    while i < n:
        c = linea[i]
        if comilla_abierta:
            if c == comilla_abierta:
                comilla_abierta = None
            i += 1
            continue
        if c in ("'", '"'):
            comilla_abierta = c
            i += 1
            continue
        if linea[i:i + m] == marcador:
            if marcador == "//" and i > 0 and linea[i - 1] == ":":
                i += 1
                continue
            return linea[:i]
        i += 1
    return linea


def _termino_en_codigo(texto_l, termino, nombre_fichero=""):
    """Gap 170/171 (revisión Fase 4 intento 2): antes se buscaba `termino in texto_l` sobre el
    TEXTO COMPLETO del fichero, así que un hook que solo DOCUMENTASE la prohibición («no hace red
    ni curl ni urllib») rompía la suite por subcadena en su propio comentario. Se mira solo la
    parte de CÓDIGO de cada línea y con frontera de "palabra" (un guion cuenta como parte del
    término — `curator-gate` no debe casar dentro de un identificador más largo, ni al revés)."""
    patron = re.compile(r"(?<![\w-])" + re.escape(termino) + r"(?![\w-])")
    for codigo in _lineas_de_codigo(texto_l, nombre_fichero):
        if patron.search(codigo):
            return True
    return False


def _rutas_script_invocadas(texto, nombre_fichero=""):
    """gap 169: rutas `.py`/`.sh` citadas en la parte de CÓDIGO de un hook/frontmatter (p. ej.
    `python3 "$SHARED/journal.py"`, `bash "hooks/mark-docs-pending.sh"`,
    `agent-kits/shared/guardrail-check.py`) — el `$VAR/` delante de una ruta no forma parte de la
    ruta de fichero real, así que se descarta junto con la barra que lo sigue. Gap 170: solo en
    código, no en un comentario que meramente MENCIONE el nombre de otro script sin invocarlo (p.
    ej. una nota de diseño que dice «esto también lo usa outbox.py» no debe hacer que el escaneo
    se vaya a leer `outbox.py` y le aplique la lista de términos)."""
    rutas = set()
    for codigo in _lineas_de_codigo(texto, nombre_fichero):
        rutas |= {m.group(0).lstrip("$/") for m in _RUTA_SCRIPT_RE.finditer(codigo)}
    return rutas


def _resolver_ruta_script(ruta_rel, root):
    """gap 169: resuelve una ruta citada (relativa al repo, o solo el nombre de fichero tras una
    variable de shell) contra `root`; si no existe tal cual, cae a buscarla por NOMBRE bajo
    `agent-kits/shared/` y `hooks/` (las dos carpetas donde viven hoy los scripts que los hooks
    invocan)."""
    candidato = os.path.normpath(os.path.join(root, ruta_rel))
    if os.path.isfile(candidato):
        return candidato
    nombre = os.path.basename(ruta_rel)
    for carpeta in (os.path.join(root, "agent-kits", "shared"), os.path.join(root, "hooks")):
        posible = os.path.join(carpeta, nombre)
        if os.path.isfile(posible):
            return posible
    return None


def _ofensores_de_scripts_invocados(rutas_rel, root, vistos, profundidad=1):
    """gap 169: sigue las invocaciones — para cada ruta `.py`/`.sh` citada por un hook o un
    frontmatter, resuelve el fichero real y le aplica la MISMA lista de términos prohibidos (con
    la misma disciplina de código/frontera de palabra del gap 170/171), salvo que esté en la
    allowlist explícita de usos locales legítimos.

    Gap 181 (revisión Fase 4 intento 3): el seguimiento era de UN SOLO NIVEL — un hook que invoca
    un script "limpio" que a su vez invoca OTRO script con `urllib` pasaba desapercibido
    (`session-journal.sh -> journal.py -> outbox.py`; `urllib` en `outbox.py` no se detectaba
    porque nadie escaneaba más allá de `journal.py`). Ahora es TRANSITIVO: las rutas `.py`/`.sh`
    que cada script resuelto invoca a su vez también se siguen, hasta
    `_MAX_PROFUNDIDAD_SEGUIMIENTO` saltos — `vistos` sigue cortando cualquier ciclo (A invoca B
    invoca A) antes de llegar a ese tope."""
    ofensores = []
    if profundidad > _MAX_PROFUNDIDAD_SEGUIMIENTO:
        return ofensores
    siguientes_rutas = set()
    for ruta_rel in sorted(rutas_rel):
        resuelta = _resolver_ruta_script(ruta_rel, root)
        if not resuelta:
            continue
        resuelta = os.path.normpath(resuelta)
        if resuelta in vistos:
            continue
        vistos.add(resuelta)
        etiqueta = os.path.relpath(resuelta, root).replace(os.sep, "/")
        if etiqueta in _ALLOWLIST_USOS_LOCALES_DE_RED:
            continue
        texto_script = _texto_o_fallo_si_no_decodifica(resuelta)
        texto_script_l = texto_script.lower()
        for termino in _TERMINOS_RED_PROHIBIDOS:
            if _termino_en_codigo(texto_script_l, termino, os.path.basename(resuelta)):
                ofensores.append((etiqueta, termino))
        siguientes_rutas |= _rutas_script_invocadas(texto_script, os.path.basename(resuelta))
    if siguientes_rutas:
        ofensores += _ofensores_de_scripts_invocados(siguientes_rutas, root, vistos, profundidad + 1)
    return ofensores


def _ofensores_de_red_en_hooks(hooks_dir=None, root=None):
    """Recorre `hooks/**` RECURSIVAMENTE (gap 154: antes solo el nivel superior) y, gap 169,
    sigue además los scripts que cada hook invoca fuera de `hooks/`."""
    hooks_dir = hooks_dir if hooks_dir is not None else HOOKS_DIR
    root = root if root is not None else ROOT
    ofensores = []
    scripts_invocados = set()
    vistos = set()
    for raiz, _dirs, ficheros in os.walk(hooks_dir):
        for nombre in sorted(ficheros):
            ruta = os.path.join(raiz, nombre)
            vistos.add(os.path.normpath(ruta))
            texto = _texto_o_fallo_si_no_decodifica(ruta)
            texto_l = texto.lower()
            for termino in _TERMINOS_RED_PROHIBIDOS:
                if _termino_en_codigo(texto_l, termino, nombre):
                    ofensores.append((os.path.relpath(ruta, hooks_dir), termino))
            scripts_invocados |= _rutas_script_invocadas(texto)
    ofensores += _ofensores_de_scripts_invocados(scripts_invocados, root, vistos)
    return ofensores


def _bloque_hooks_frontmatter(texto):
    """gap 168 (revisión Fase 4 intento 2): la versión anterior (`(?:[ \\t]+\\S.*\\n?)*`) exigía
    que TODAS las líneas del bloque estuvieran indentadas y no vacías — se cortaba en la primera
    línea en blanco o en el primer comentario a columna 0 intercalados dentro de un `hooks:` real
    (ambos son YAML válido dentro de un bloque de mapeo, y de hecho `agents/implementer.md` y
    `agents/architect.md` tienen un comentario a columna 0 justo debajo de su bloque `hooks:`,
    antes de `dependencies:`). Ahora se extrae TODO desde `hooks:` hasta la siguiente CLAVE de
    nivel 0 del frontmatter (`^[A-Za-z_][\\w-]*:` sin indentar) o el cierre `---`, incluyendo
    líneas en blanco y comentarios intercalados."""
    # `splitlines()` normaliza CRLF/LF por igual (gap 168, hallado al escribir el test en disco en
    # Windows: un `\r\n` tras `hooks:` no casaba con un `\n` literal en la regex anterior).
    todas = texto.splitlines(keepends=True)
    inicio = None
    for idx, linea in enumerate(todas):
        if linea.rstrip("\r\n") == "hooks:":
            inicio = idx + 1
            break
    if inicio is None:
        return None
    clave_top_re = re.compile(r"^[A-Za-z_][\w-]*:(\s|$)")
    lineas = []
    for linea in todas[inicio:]:
        cuerpo = linea.rstrip("\r\n")
        if cuerpo.strip() == "---":
            break
        if cuerpo[:1] not in (" ", "\t") and cuerpo.strip() != "" and clave_top_re.match(cuerpo):
            break
        lineas.append(linea)
    return "".join(lineas)


def _ofensores_de_red_en_frontmatter_agentes(agents_dir=None, root=None):
    """`hooks:` en el frontmatter de `agents/*.md` (gap 154: nadie lo miraba; gap 168: el corte
    prematuro en blanco/comentario; gap 169: sigue los scripts que el bloque invoca)."""
    agents_dir = agents_dir if agents_dir is not None else os.path.join(ROOT, "agents")
    root = root if root is not None else ROOT
    if not os.path.isdir(agents_dir):
        return []
    ofensores = []
    scripts_invocados = set()
    vistos = set()
    for nombre in sorted(os.listdir(agents_dir)):
        if not nombre.endswith(".md"):
            continue
        ruta = os.path.join(agents_dir, nombre)
        texto = _texto_o_fallo_si_no_decodifica(ruta)
        bloque = _bloque_hooks_frontmatter(texto)
        if bloque is None:
            continue
        bloque_l = bloque.lower()
        for termino in _TERMINOS_RED_PROHIBIDOS:
            if _termino_en_codigo(bloque_l, termino, nombre):
                ofensores.append((nombre, termino))
        scripts_invocados |= _rutas_script_invocadas(bloque)
    ofensores += _ofensores_de_scripts_invocados(scripts_invocados, root, vistos)
    return ofensores


def test_ningun_hook_ni_frontmatter_de_agente_invoca_red_ni_scripts_de_publicacion():
    """CA de la spec «red desde hooks» fuera de alcance: ningún hook del ciclo (`hooks/**`,
    recursivo, siguiendo los scripts que invoca) ni el frontmatter `hooks:` de ningún agente debe
    disparar `knowledge-sync.py` ni `curator-gate.py` (hacen red o mutan `docs/knowledge/`) NI
    hacer red por su cuenta — los hooks del ciclo (PostToolUse, SubagentStop, SessionStart/End,
    UserPromptSubmit) SOLO informan (systemMessage/additionalContext), nunca ejecutan lógica de
    publicación ni abren conexiones."""
    ofensores = _ofensores_de_red_en_hooks() + _ofensores_de_red_en_frontmatter_agentes()
    assert ofensores == [], f"hook/frontmatter invoca red o script de publicación: {ofensores}"


def test_mutante_hook_con_curl_en_subcarpeta_muere(tmp_path):
    """Mutante (gap 141): un hook con `curl https://…` debe morir — y en una SUBCARPETA de
    `hooks/`, para probar la recursión del gap 154 (la lista anterior no recorría subdirectorios)."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "malo.sh").write_text("#!/bin/sh\ncurl https://ejemplo.invalido/x\n", encoding="utf-8")
    ofensores = _ofensores_de_red_en_hooks(str(tmp_path), root=str(tmp_path))
    assert ofensores == [(os.path.join("sub", "malo.sh"), "curl")]


def test_mutante_hook_no_decodificable_es_fallo_no_skip(tmp_path):
    """Gap 154: un fichero no UTF-8 bajo `hooks/` debe hacer FALLAR el escaneo (`AssertionError`),
    no saltarse en silencio — un hook corrupto que ADEMÁS invoque red no debe colarse."""
    (tmp_path / "binario.bin").write_bytes(b"\xff\xfe\x00\x01\x02\x03")
    with pytest.raises(AssertionError):
        _ofensores_de_red_en_hooks(str(tmp_path), root=str(tmp_path))


def test_mutante_frontmatter_de_agente_con_urllib_muere(tmp_path):
    """Mutante (gap 141/154): un `command` de `hooks:` en el frontmatter de un agente que use
    `urllib.request.urlopen` debe morir aunque no exista NINGÚN fichero bajo `hooks/`."""
    contenido = (
        "---\nname: falso\nmodel: sonnet\nhooks:\n"
        "  PreToolUse:\n"
        "    - matcher: \"Write\"\n"
        "      hooks:\n"
        "        - type: command\n"
        "          command: 'python -c \"import urllib.request; "
        "urllib.request.urlopen(1)\"'\n"
        "---\n\n# Falso\n"
    )
    (tmp_path / "falso.md").write_text(contenido, encoding="utf-8")
    ofensores = _ofensores_de_red_en_frontmatter_agentes(str(tmp_path), root=str(tmp_path))
    assert ("falso.md", "urllib") in ofensores
    assert ("falso.md", "urlopen") in ofensores


def test_mutante_frontmatter_con_segundo_matcher_tras_linea_en_blanco_muere(tmp_path):
    """Gap 168: la regex anterior cortaba el bloque `hooks:` en la primera línea en blanco — un
    SEGUNDO matcher, separado del primero por una línea vacía (YAML válido dentro del mismo mapeo
    `hooks:`), con `curl` en su `command`, pasaba desapercibido (`0 ofensores` cuando debía haber
    1)."""
    contenido = (
        "---\nname: falso\nmodel: sonnet\nhooks:\n"
        "  PreToolUse:\n"
        "    - matcher: \"Write\"\n"
        "      hooks:\n"
        "        - type: command\n"
        "          command: 'echo hola'\n"
        "\n"
        "    - matcher: \"Bash\"\n"
        "      hooks:\n"
        "        - type: command\n"
        "          command: 'curl https://ejemplo.invalido/x'\n"
        "---\n\n# Falso\n"
    )
    (tmp_path / "falso.md").write_text(contenido, encoding="utf-8")
    ofensores = _ofensores_de_red_en_frontmatter_agentes(str(tmp_path), root=str(tmp_path))
    assert ("falso.md", "curl") in ofensores


def test_mutante_frontmatter_con_comentario_a_columna_0_no_corta_el_bloque(tmp_path):
    """Gap 168: un comentario YAML a columna 0 intercalado en el bloque `hooks:` (patrón real de
    `agents/implementer.md`/`agents/architect.md`, que tienen justo un `# Dependencias
    declaradas...` entre `hooks:` y `dependencies:`) tampoco debía cortar el escaneo — un segundo
    matcher DESPUÉS de ese comentario con `wget` debía seguir detectándose."""
    contenido = (
        "---\nname: falso\nmodel: sonnet\nhooks:\n"
        "  PreToolUse:\n"
        "    - matcher: \"Write\"\n"
        "      hooks:\n"
        "        - type: command\n"
        "          command: 'echo hola'\n"
        "# comentario a columna 0, no es una clave de nivel 0\n"
        "    - matcher: \"Bash\"\n"
        "      hooks:\n"
        "        - type: command\n"
        "          command: 'wget https://ejemplo.invalido/x'\n"
        "---\n\n# Falso\n"
    )
    (tmp_path / "falso.md").write_text(contenido, encoding="utf-8")
    ofensores = _ofensores_de_red_en_frontmatter_agentes(str(tmp_path), root=str(tmp_path))
    assert ("falso.md", "wget") in ofensores


def test_mutante_frontmatter_se_detiene_en_la_siguiente_clave_de_nivel_0(tmp_path):
    """Gap 168 (complemento): el bloque `hooks:` no debe devorar el resto del frontmatter — un
    término prohibido que viva en OTRA clave de nivel 0 (aquí `description:`, tras `hooks:`) no
    cuenta como parte del bloque `hooks:` (el frontmatter real ya prohíbe esos términos fuera de
    `hooks:` con otras reglas del propio linter del plugin, no con este escaneo)."""
    contenido = (
        "---\nname: falso\nmodel: sonnet\nhooks:\n"
        "  PreToolUse:\n"
        "    - matcher: \"Write\"\n"
        "      hooks:\n"
        "        - type: command\n"
        "          command: 'echo hola'\n"
        "description: menciona curl solo como ejemplo de herramienta, no la ejecuta\n"
        "---\n\n# Falso\n"
    )
    (tmp_path / "falso.md").write_text(contenido, encoding="utf-8")
    ofensores = _ofensores_de_red_en_frontmatter_agentes(str(tmp_path), root=str(tmp_path))
    assert ofensores == []


def test_mutante_script_invocado_por_hook_con_urllib_muere(tmp_path):
    """Gap 169: el escaneo anterior solo miraba los ficheros DIRECTOS de `hooks/**` — un hook que
    invoque un script fuera de `hooks/` (típico: `agent-kits/shared/*.py`) con `import
    urllib.request` dentro pasaba desapercibido. Se construye un repo sintético en `tmp_path` con
    su propio `agent-kits/shared/ayudante.py` para no depender del árbol real."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    shared_dir = tmp_path / "agent-kits" / "shared"
    shared_dir.mkdir(parents=True)
    (hooks_dir / "invoca.sh").write_text(
        "#!/bin/sh\npython3 \"$CLAUDE_PLUGIN_ROOT/agent-kits/shared/ayudante.py\"\n",
        encoding="utf-8")
    (shared_dir / "ayudante.py").write_text(
        "import urllib.request\nurllib.request.urlopen('http://x')\n", encoding="utf-8")
    ofensores = _ofensores_de_red_en_hooks(str(hooks_dir), root=str(tmp_path))
    assert ("agent-kits/shared/ayudante.py", "urllib") in ofensores
    assert ("agent-kits/shared/ayudante.py", "urlopen") in ofensores


def test_mutante_script_invocado_por_frontmatter_con_socket_muere(tmp_path):
    """Gap 169: mismo criterio que el test anterior, pero siguiendo la invocación desde el
    frontmatter `hooks:` de un agente (no desde `hooks/**`)."""
    shared_dir = tmp_path / "agent-kits" / "shared"
    shared_dir.mkdir(parents=True)
    (shared_dir / "ayudante2.py").write_text(
        "import socket\nsocket.gethostbyname('x')\n", encoding="utf-8")
    contenido = (
        "---\nname: falso\nmodel: sonnet\nhooks:\n"
        "  PreToolUse:\n"
        "    - matcher: \"Write\"\n"
        "      hooks:\n"
        "        - type: command\n"
        "          command: 'python3 \"agent-kits/shared/ayudante2.py\"'\n"
        "---\n\n# Falso\n"
    )
    (tmp_path / "falso.md").write_text(contenido, encoding="utf-8")
    ofensores = _ofensores_de_red_en_frontmatter_agentes(str(tmp_path), root=str(tmp_path))
    assert ("agent-kits/shared/ayudante2.py", "socket") in ofensores


def test_gap181_seguimiento_transitivo_de_dos_saltos_muere(tmp_path):
    """Gap 181 (revisión Fase 4 intento 3): el seguimiento de invocaciones era de UN SOLO NIVEL —
    `hooks/invoca.sh` invoca `nivel1.py` (limpio), que a su vez invoca `nivel2.py` (con
    `urllib`); antes de este fix `nivel2.py` nunca se escaneaba porque nadie seguía lo que
    `nivel1.py` invoca. Reproduce el patrón real `session-journal.sh -> journal.py ->
    outbox.py`."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    shared_dir = tmp_path / "agent-kits" / "shared"
    shared_dir.mkdir(parents=True)
    (hooks_dir / "invoca.sh").write_text(
        "#!/bin/sh\npython3 \"$CLAUDE_PLUGIN_ROOT/agent-kits/shared/nivel1.py\"\n",
        encoding="utf-8")
    (shared_dir / "nivel1.py").write_text(
        "import subprocess\nsubprocess.run(['python3', 'agent-kits/shared/nivel2.py'])\n",
        encoding="utf-8")
    (shared_dir / "nivel2.py").write_text(
        "import urllib.request\nurllib.request.urlopen('http://x')\n", encoding="utf-8")
    ofensores = _ofensores_de_red_en_hooks(str(hooks_dir), root=str(tmp_path))
    assert ("agent-kits/shared/nivel2.py", "urllib") in ofensores
    assert ("agent-kits/shared/nivel2.py", "urlopen") in ofensores
    # nivel1.py en sí no menciona ningún término prohibido en su propio código.
    assert all(etiqueta != "agent-kits/shared/nivel1.py" for etiqueta, _termino in ofensores)


def test_gap181_ciclo_de_invocaciones_no_cuelga(tmp_path):
    """Gap 181: un ciclo real de invocaciones (A invoca B, B invoca A) no debe colgar el escaneo
    ni recursión infinita — `vistos` corta el ciclo antes de perseguirlo de nuevo, y el ofensor de
    `curl` en `nivel_b.py` se detecta igualmente."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    shared_dir = tmp_path / "agent-kits" / "shared"
    shared_dir.mkdir(parents=True)
    (hooks_dir / "invoca.sh").write_text(
        "#!/bin/sh\npython3 \"$CLAUDE_PLUGIN_ROOT/agent-kits/shared/nivel_a.py\"\n",
        encoding="utf-8")
    (shared_dir / "nivel_a.py").write_text(
        "import subprocess\nsubprocess.run(['python3', 'agent-kits/shared/nivel_b.py'])\n",
        encoding="utf-8")
    (shared_dir / "nivel_b.py").write_text(
        "import subprocess\n"
        "subprocess.run(['python3', 'agent-kits/shared/nivel_a.py'])\n"
        "subprocess.run(['curl', 'https://ejemplo.invalido/x'])\n",
        encoding="utf-8")
    ofensores = _ofensores_de_red_en_hooks(str(hooks_dir), root=str(tmp_path))
    assert ("agent-kits/shared/nivel_b.py", "curl") in ofensores


def test_gap181_docstring_de_script_seguido_no_arrastra_menciones_de_otros_ficheros(tmp_path):
    """Gap 181 (hallado al implementar el seguimiento transitivo, no en la lista original de la
    revisión): un script seguido transitivamente puede tener un DOCSTRING extenso (patrón real de
    este repo) que MENCIONE de pasada la ruta de otro fichero real — sin invocarlo. Antes del
    recorte de docstrings triple-comillados, esa mención colaba el fichero mencionado en el
    escaneo (en una corrida real: `agent-kits/shared/outbox.py` mencionaba `knowledge-sync.py` en
    su docstring y arrastraba, encadenado, `tests/test_console_encoding.py`). Aquí: `nivel1.py`
    (seguido desde `hooks/invoca.sh`) documenta en su docstring que «esto lo usa también
    otro_real.py», y `otro_real.py` (que SÍ existe en `tmp_path` y SÍ tiene `curl` en su código)
    NO debe aparecer entre los ofensores porque nadie lo invoca de verdad."""
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    (hooks_dir / "invoca.sh").write_text(
        "#!/bin/sh\npython3 \"$CLAUDE_PLUGIN_ROOT/otro_real.py\"\n", encoding="utf-8")
    (tmp_path / "otro_real.py").write_text(
        '"""Docstring que documenta, sin invocar, otro_real2.py."""\n'
        "print('no hace red')\n",
        encoding="utf-8")
    (tmp_path / "otro_real2.py").write_text(
        "import subprocess\nsubprocess.run(['curl', 'https://ejemplo.invalido/x'])\n",
        encoding="utf-8")
    # `otro_real.py` no vive bajo `agent-kits/shared/` ni `hooks/`, así que `_resolver_ruta_script`
    # no lo encuentra por nombre — se ejercita directamente `_ofensores_de_scripts_invocados` con
    # la ruta exacta para centrar el test en el recorte de docstrings, no en la resolución de
    # rutas (ya cubierta por otros tests de esta suite).
    ofensores = _ofensores_de_scripts_invocados({"otro_real.py"}, str(tmp_path), set())
    assert ofensores == []
    etiquetas = {etiqueta for etiqueta, _termino in ofensores}
    assert "otro_real2.py" not in etiquetas


def test_falso_positivo_comentario_documentando_la_prohibicion_no_rompe_la_suite(tmp_path):
    """Gap 170: un hook que DOCUMENTE la prohibición («no hace red ni curl ni urllib») en un
    comentario no debe contarse como ofensor — antes se buscaba la subcadena sobre el texto
    COMPLETO del fichero, sin distinguir código de comentario."""
    (tmp_path / "documentado.sh").write_text(
        "#!/bin/sh\n"
        "# Este hook no hace red (ni curl ni urllib): solo informa via systemMessage.\n"
        "echo '{\"systemMessage\": \"ok\"}'\n",
        encoding="utf-8")
    ofensores = _ofensores_de_red_en_hooks(str(tmp_path), root=str(tmp_path))
    assert ofensores == []


def test_falso_positivo_comentario_en_frontmatter_no_rompe_la_suite(tmp_path):
    """Gap 170, mismo criterio en el frontmatter: un comentario dentro del bloque `hooks:` que
    documente la prohibición no debe contarse."""
    contenido = (
        "---\nname: falso\nmodel: sonnet\nhooks:\n"
        "  PreToolUse:\n"
        "    - matcher: \"Write\"\n"
        "      hooks:\n"
        "        - type: command\n"
        "          command: 'echo hola'\n"
        "          # este command no hace red (ni curl ni urllib)\n"
        "---\n\n# Falso\n"
    )
    (tmp_path / "falso.md").write_text(contenido, encoding="utf-8")
    ofensores = _ofensores_de_red_en_frontmatter_agentes(str(tmp_path), root=str(tmp_path))
    assert ofensores == []


def test_regresion_gap178_termino_tras_comilla_con_almohadilla_se_detecta(tmp_path):
    """Gap 178 (revisión Fase 4 intento 3): `sed "s/#.*//" x; curl …` tiene un `#` DENTRO de una
    cadena entrecomillada (`"s/#.*//"`) — el corte naive en el primer `#` de la línea perdía el
    `curl` que viene después del `;`. Con la cadena reconocida, el `#` interior no cuenta como
    marcador y `curl` sigue siendo código."""
    (tmp_path / "malo.sh").write_text(
        "#!/bin/sh\n" 'sed "s/#.*//" x; curl https://ejemplo.invalido/x\n',
        encoding="utf-8")
    ofensores = _ofensores_de_red_en_hooks(str(tmp_path), root=str(tmp_path))
    assert ("malo.sh", "curl") in ofensores


def test_regresion_gap178_js_con_url_en_comillas_no_esconde_termino_posterior(tmp_path):
    """Gap 178, mismo criterio en `.js` (marcador `//`): una URL entrecomillada (`"https://evil"`)
    no debe cortar la línea antes de un `curl` que aparezca después — ni por estar dentro de
    comillas, ni porque la `//` de `https://` va precedida de `:`."""
    (tmp_path / "malo.js").write_text(
        'const u = "https://evil"; curl(u);\n', encoding="utf-8")
    ofensores = _ofensores_de_red_en_hooks(str(tmp_path), root=str(tmp_path))
    assert (os.path.join("malo.js"), "curl") in ofensores


def test_mutante_curator_gate_sin_extension_muere(tmp_path):
    """Gap 171: `knowledge-sync` sin extensión ya estaba en la lista; `curator-gate` sin extensión
    (un `command` puede invocar el módulo por su nombre, sin `.py`, según el shell) no lo estaba —
    asimetría sin motivo entre los dos gemelos de publicación/mutación."""
    (tmp_path / "malo.sh").write_text(
        "#!/bin/sh\ncurator-gate --decision approve --category DECISION\n",
        encoding="utf-8")
    ofensores = _ofensores_de_red_en_hooks(str(tmp_path), root=str(tmp_path))
    assert ("malo.sh", "curator-gate") in ofensores
