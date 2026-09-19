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


def test_health_url_host_publico_se_rechaza_sin_conexion():
    salud = markdown_export.health({"health": {"url": "http://example.com/health", "timeout_ms": 100}})
    assert salud["estado"] == "error"
    assert "no local" in salud["detalle"]


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
        httpd.server_close()  # gap 153: sin esto el socket queda en TIME_WAIT/abierto
        hilo.join(timeout=2)
        assert not hilo.is_alive(), "el hilo del servidor de test no terminó (gap 153)"


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


# ------------------------------------------------------------------ hooks sin red ----

# gap 141/154 (revisión de dos lentes, Fase 4 intento 1): la lista anterior solo buscaba los dos
# nombres de script (`knowledge-sync.py`/`curator-gate.py`) en los ficheros DIRECTOS de `hooks/`
# (sin recursión), tragaba `UnicodeDecodeError` con un `continue` silencioso (un hook binario o
# corrupto quedaba sin analizar, no como fallo), y no miraba el frontmatter `hooks:` de
# `agents/*.md` (un agente puede declarar un hook `command` inline con la misma red prohibida sin
# que exista ningún fichero bajo `hooks/`). Se amplía a los términos de red/publicación que la
# revisión señaló (`urllib`, `urlopen`, `socket`, `http.client`, `requests`, `curl`, `wget`,
# `Invoke-WebRequest`, `markdown_export`) y a `knowledge-sync` SIN extensión (un `command` puede
# invocar el script por su nombre de módulo, sin `.py`, según el shell).
_TERMINOS_RED_PROHIBIDOS = (
    "knowledge-sync.py", "knowledge-sync", "curator-gate.py", "markdown_export",
    "urllib", "urlopen", "socket", "http.client", "requests", "curl", "wget",
    "invoke-webrequest",
)

_HOOKS_FRONTMATTER_RE = None  # se compila perezosamente (evita el import de `re` en el módulo)


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


def _ofensores_de_red_en_hooks(hooks_dir=None):
    """Recorre `hooks/**` RECURSIVAMENTE (gap 154: antes solo el nivel superior)."""
    hooks_dir = hooks_dir if hooks_dir is not None else HOOKS_DIR
    ofensores = []
    for raiz, _dirs, ficheros in os.walk(hooks_dir):
        for nombre in sorted(ficheros):
            ruta = os.path.join(raiz, nombre)
            texto_l = _texto_o_fallo_si_no_decodifica(ruta).lower()
            for termino in _TERMINOS_RED_PROHIBIDOS:
                if termino in texto_l:
                    ofensores.append((os.path.relpath(ruta, hooks_dir), termino))
    return ofensores


def _ofensores_de_red_en_frontmatter_agentes(agents_dir=None):
    """`hooks:` en el frontmatter de `agents/*.md` (gap 154: nadie lo miraba)."""
    import re
    agents_dir = agents_dir if agents_dir is not None else os.path.join(ROOT, "agents")
    if not os.path.isdir(agents_dir):
        return []
    patron = re.compile(r"(?m)^hooks:\s*\n((?:[ \t]+\S.*\n?)*)")
    ofensores = []
    for nombre in sorted(os.listdir(agents_dir)):
        if not nombre.endswith(".md"):
            continue
        ruta = os.path.join(agents_dir, nombre)
        texto = _texto_o_fallo_si_no_decodifica(ruta)
        m = patron.search(texto)
        if not m:
            continue
        bloque = m.group(1).lower()
        for termino in _TERMINOS_RED_PROHIBIDOS:
            if termino in bloque:
                ofensores.append((nombre, termino))
    return ofensores


def test_ningun_hook_ni_frontmatter_de_agente_invoca_red_ni_scripts_de_publicacion():
    """CA de la spec «red desde hooks» fuera de alcance: ningún hook del ciclo (`hooks/**`,
    recursivo) ni el frontmatter `hooks:` de ningún agente debe disparar `knowledge-sync.py` ni
    `curator-gate.py` (hacen red o mutan `docs/knowledge/`) NI hacer red por su cuenta — los hooks
    del ciclo (PostToolUse, SubagentStop, SessionStart/End, UserPromptSubmit) SOLO informan
    (systemMessage/additionalContext), nunca ejecutan lógica de publicación ni abren conexiones."""
    ofensores = _ofensores_de_red_en_hooks() + _ofensores_de_red_en_frontmatter_agentes()
    assert ofensores == [], f"hook/frontmatter invoca red o script de publicación: {ofensores}"


def test_mutante_hook_con_curl_en_subcarpeta_muere(tmp_path):
    """Mutante (gap 141): un hook con `curl https://…` debe morir — y en una SUBCARPETA de
    `hooks/`, para probar la recursión del gap 154 (la lista anterior no recorría subdirectorios)."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "malo.sh").write_text("#!/bin/sh\ncurl https://ejemplo.invalido/x\n", encoding="utf-8")
    ofensores = _ofensores_de_red_en_hooks(str(tmp_path))
    assert ofensores == [(os.path.join("sub", "malo.sh"), "curl")]


def test_mutante_hook_no_decodificable_es_fallo_no_skip(tmp_path):
    """Gap 154: un fichero no UTF-8 bajo `hooks/` debe hacer FALLAR el escaneo (`AssertionError`),
    no saltarse en silencio — un hook corrupto que ADEMÁS invoque red no debe colarse."""
    (tmp_path / "binario.bin").write_bytes(b"\xff\xfe\x00\x01\x02\x03")
    with pytest.raises(AssertionError):
        _ofensores_de_red_en_hooks(str(tmp_path))


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
    ofensores = _ofensores_de_red_en_frontmatter_agentes(str(tmp_path))
    assert ("falso.md", "urllib") in ofensores
    assert ("falso.md", "urlopen") in ofensores
