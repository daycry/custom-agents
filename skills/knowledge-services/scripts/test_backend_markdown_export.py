#!/usr/bin/env python3
"""Tests de `backends/markdown_export.py` (T-08, adaptador Kwipu). Sin red: `health()`/`verify()`
se prueban contra un `http.server` local efímero que sirve las fixtures REALES capturadas del
stack (`fixtures/kwipu-health-2026-09-18.json`, `fixtures/kwipu-graph-snapshot-2026-09-18.json`),
nunca contra la red real."""
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
BACKENDS_DIR = os.path.normpath(os.path.join(HERE, "..", "backends"))
FIXTURES = os.path.join(HERE, "fixtures")


def _cargar():
    spec = importlib.util.spec_from_file_location(
        "ks_backend_markdown_export", os.path.join(BACKENDS_DIR, "markdown_export.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _leer_fixture(nombre):
    with open(os.path.join(FIXTURES, nombre), "r", encoding="utf-8") as f:
        return f.read()


class _ServidorFixturas(BaseHTTPRequestHandler):
    respuestas = {}  # ruta -> (status, bytes)

    def _responder(self):
        cuerpo = self.respuestas.get(self.path)
        if cuerpo is None:
            self.send_response(404)
            self.end_headers()
            return
        status, datos = cuerpo
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):  # noqa: N802 - nombre impuesto por BaseHTTPRequestHandler
        self._responder()

    def log_message(self, *args, **kwargs):
        pass  # silencia el log por defecto de http.server en la salida de test


class _ServidorFixturasContext:
    """Levanta un `HTTPServer` en un hilo, en `127.0.0.1` y puerto efímero, sirviendo SOLO las
    fixtures reales del stack — nunca red real, nunca un mock que invente forma de respuesta."""

    def __init__(self, respuestas):
        self._respuestas = respuestas

    def __enter__(self):
        handler = type("Handler", (_ServidorFixturas,), {"respuestas": self._respuestas})
        self.httpd = HTTPServer(("127.0.0.1", 0), handler)
        self.puerto = self.httpd.server_address[1]
        self.hilo = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.hilo.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    @property
    def base_url(self):
        return f"http://127.0.0.1:{self.puerto}"


def _entrada(id_="mr.pattern.fast-curve-derailment", version=1, category="PATTERN",
             evidencia="multiple_validated_cases", cuerpo="Cuerpo de la entrada.\n"):
    return {
        "id": id_, "version": version, "category": category, "evidencia": evidencia,
        "fuentes": ["docs/x.md"], "tags": ["curva"], "modo": "completo", "cuerpo": cuerpo,
    }


class TestMarkdownExportPlanApply(unittest.TestCase):
    def setUp(self):
        self.mod = _cargar()
        self.tmp = tempfile.mkdtemp(prefix="ks-export-")
        self.export_dir = os.path.join(self.tmp, "kwipu-export")
        self.cfg = {"export_dir": self.export_dir,
                    "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_apply_escribe_un_markdown_por_entrada_con_frontmatter_ca17(self):
        entradas = [_entrada()]
        ops = self.mod.plan(entradas, self.cfg)
        resultado = self.mod.apply(ops, self.cfg)
        self.assertEqual(resultado.get("escritos"), 1)
        ruta = os.path.join(self.export_dir, "mr.pattern.fast-curve-derailment.md")
        self.assertTrue(os.path.isfile(ruta))
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
        for campo in ("knowledge_id: mr.pattern.fast-curve-derailment", "project: mr",
                      "scope: project", "category: PATTERN", "source: agent",
                      "confidence: medium", "version: 1", "hash:"):
            self.assertIn(campo, texto)
        self.assertIn("Cuerpo de la entrada.", texto)

    def test_confianza_se_deriva_del_nivel_de_evidencia(self):
        casos = {"observation": "confidence: low", "single_case": "confidence: low",
                 "validated_case": "confidence: medium",
                 "multiple_validated_cases": "confidence: medium",
                 "human_confirmed_rule": "confidence: high",
                 "nivel-desconocido-del-proyecto": "confidence: medium"}
        for evidencia, esperado in casos.items():
            with self.subTest(evidencia=evidencia):
                entradas = [_entrada(id_=f"mr.pattern.caso-{evidencia}", evidencia=evidencia)]
                ops = self.mod.plan(entradas, self.cfg)
                self.mod.apply(ops, self.cfg)
                ruta = os.path.join(self.export_dir, f"mr.pattern.caso-{evidencia}.md")
                with open(ruta, "r", encoding="utf-8") as f:
                    self.assertIn(esperado, f.read())

    def test_manifest_json_tiene_hash_estable_y_es_idempotente(self):
        entradas = [_entrada()]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        with open(os.path.join(self.export_dir, "manifest.json"), "r", encoding="utf-8") as f:
            m1 = json.load(f)
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        with open(os.path.join(self.export_dir, "manifest.json"), "r", encoding="utf-8") as f:
            m2 = json.load(f)
        self.assertEqual(m1["entries"], m2["entries"])
        self.assertIn("mr.pattern.fast-curve-derailment", m1["entries"])
        self.assertEqual(len(m1["entries"]["mr.pattern.fast-curve-derailment"]["hash"]), 64)

    def test_plan_retira_entradas_que_salieron_de_approved(self):
        primera = [_entrada(id_="mr.pattern.a"), _entrada(id_="mr.pattern.b")]
        self.mod.apply(self.mod.plan(primera, self.cfg), self.cfg)
        self.assertTrue(os.path.isfile(os.path.join(self.export_dir, "mr.pattern.b.md")))
        segunda = [_entrada(id_="mr.pattern.a")]
        ops = self.mod.plan(segunda, self.cfg)
        acciones = {op["accion"] for op in ops}
        self.assertIn("revoke", acciones)
        self.mod.apply(ops, self.cfg)
        self.assertFalse(os.path.exists(os.path.join(self.export_dir, "mr.pattern.b.md")))
        self.assertTrue(os.path.isfile(os.path.join(self.export_dir, "mr.pattern.a.md")))

    def test_rebuild_reproduce_el_mismo_manifiesto(self):
        entradas = [_entrada(id_="mr.pattern.a"), _entrada(id_="mr.pattern.b")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        with open(os.path.join(self.export_dir, "manifest.json"), "r", encoding="utf-8") as f:
            antes = json.load(f)
        self.mod.rebuild(entradas, self.cfg)
        with open(os.path.join(self.export_dir, "manifest.json"), "r", encoding="utf-8") as f:
            despues = json.load(f)
        self.assertEqual(antes["entries"], despues["entries"])

    def test_revoke_retira_el_fichero_y_anota_el_manifiesto(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ruta = os.path.join(self.export_dir, "mr.pattern.a.md")
        self.assertTrue(os.path.isfile(ruta))
        resultado = self.mod.revoke("mr.pattern.a", self.cfg)
        self.assertTrue(resultado.get("revocado"))
        self.assertFalse(os.path.exists(ruta))
        with open(os.path.join(self.export_dir, "manifest.json"), "r", encoding="utf-8") as f:
            m = json.load(f)
        self.assertNotIn("mr.pattern.a", m["entries"])

    def test_revoke_de_id_inexistente_es_no_op_declarado(self):
        os.makedirs(self.export_dir, exist_ok=True)
        resultado = self.mod.revoke("mr.pattern.no-existe", self.cfg)
        self.assertFalse(resultado.get("revocado"))

    def test_apply_nunca_lanza_con_entrada_vacia(self):
        resultado = self.mod.apply(self.mod.plan([], self.cfg), self.cfg)
        self.assertEqual(resultado.get("escritos"), 0)


class TestMarkdownExportHealth(unittest.TestCase):
    def setUp(self):
        self.mod = _cargar()

    def test_health_sano_con_fixture_real_status_ok(self):
        cuerpo = _leer_fixture("kwipu-health-2026-09-18.json").encode("utf-8")
        with _ServidorFixturasContext({"/health": (200, cuerpo)}) as srv:
            cfg = {"health": {"url": f"{srv.base_url}/health", "timeout_ms": 2000}}
            salud = self.mod.health(cfg)
        self.assertEqual(salud["estado"], "sano")
        self.assertIn("detalle", salud)

    def test_health_degradado_si_property_graph_no_esta_ok(self):
        payload = json.loads(_leer_fixture("kwipu-health-2026-09-18.json"))
        payload["property_graph"]["status"] = "error"
        cuerpo = json.dumps(payload).encode("utf-8")
        with _ServidorFixturasContext({"/health": (200, cuerpo)}) as srv:
            cfg = {"health": {"url": f"{srv.base_url}/health", "timeout_ms": 2000}}
            salud = self.mod.health(cfg)
        self.assertEqual(salud["estado"], "degradado")

    def test_health_degradado_si_status_top_level_es_degraded(self):
        payload = json.loads(_leer_fixture("kwipu-health-2026-09-18.json"))
        payload["status"] = "degraded"
        cuerpo = json.dumps(payload).encode("utf-8")
        with _ServidorFixturasContext({"/health": (200, cuerpo)}) as srv:
            cfg = {"health": {"url": f"{srv.base_url}/health", "timeout_ms": 2000}}
            salud = self.mod.health(cfg)
        self.assertEqual(salud["estado"], "degradado")

    def test_health_503_es_degradado_no_off(self):
        """gap 92 (fix1 2026-09-18): un bridge VIVO pero roto (503, p. ej. embedder caido) no es
        indistinguible de un stack apagado — `off` daria el remedio equivocado (levantar el stack en
        vez de mirar el log del bridge)."""
        with _ServidorFixturasContext({"/health": (503, b'{"error":"embedder unavailable"}')}) as srv:
            cfg = {"health": {"url": f"{srv.base_url}/health", "timeout_ms": 2000}}
            salud = self.mod.health(cfg)
        self.assertEqual(salud["estado"], "degradado")
        self.assertIn("503", salud["detalle"])

    def test_health_404_sigue_siendo_error(self):
        """Contraste del gap 92: un 4xx (URL mal configurada, no bridge roto) sigue siendo `error`,
        no `degradado`."""
        with _ServidorFixturasContext({"/health": (404, b"not found")}) as srv:
            cfg = {"health": {"url": f"{srv.base_url}/health", "timeout_ms": 2000}}
            salud = self.mod.health(cfg)
        self.assertEqual(salud["estado"], "error")

    def test_health_error_con_json_malformado(self):
        with _ServidorFixturasContext({"/health": (200, b"esto no es json")}) as srv:
            cfg = {"health": {"url": f"{srv.base_url}/health", "timeout_ms": 2000}}
            salud = self.mod.health(cfg)
        self.assertEqual(salud["estado"], "error")

    def test_health_off_sin_red(self):
        # Puerto 1 en localhost: conexión rechazada de inmediato, nunca una excepción sin capturar.
        cfg = {"health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 200}}
        salud = self.mod.health(cfg)
        self.assertEqual(salud["estado"], "off")

    def test_health_off_sin_url_configurada(self):
        salud = self.mod.health({"health": {}})
        self.assertEqual(salud["estado"], "off")


class TestMarkdownExportVerify(unittest.TestCase):
    def setUp(self):
        self.mod = _cargar()
        self.tmp = tempfile.mkdtemp(prefix="ks-export-verify-")
        self.export_dir = os.path.join(self.tmp, "kwipu-export")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_verify_ok_cuando_el_export_esta_en_el_snapshot(self):
        entradas = [_entrada(id_="mr.pattern.readme", cuerpo="x")]
        cfg = {"export_dir": self.export_dir,
                "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}
        self.mod.apply(self.mod.plan(entradas, cfg), cfg)
        # Renombra el export para que su file_name coincida con el snapshot real (README.md).
        os.replace(os.path.join(self.export_dir, "mr.pattern.readme.md"),
                   os.path.join(self.export_dir, "README.md"))
        manifest_path = os.path.join(self.export_dir, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
        m["entries"]["mr.pattern.readme"]["ruta_relativa"] = "README.md"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        cuerpo = _leer_fixture("kwipu-graph-snapshot-2026-09-18.json").encode("utf-8")
        with _ServidorFixturasContext({"/graph/snapshot": (200, cuerpo)}) as srv:
            cfg["health"]["url"] = f"{srv.base_url}/health"
            resultado = self.mod.verify(cfg)
        self.assertTrue(resultado["ok"])
        self.assertEqual(resultado["desfase"], [])

    def test_verify_detecta_desfase_y_nombra_el_remedio_sin_ejecutarlo(self):
        entradas = [_entrada(id_="mr.pattern.huerfano", cuerpo="x")]
        cfg = {"export_dir": self.export_dir,
                "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}
        self.mod.apply(self.mod.plan(entradas, cfg), cfg)
        cuerpo = _leer_fixture("kwipu-graph-snapshot-2026-09-18.json").encode("utf-8")
        with _ServidorFixturasContext({"/graph/snapshot": (200, cuerpo)}) as srv:
            cfg["health"]["url"] = f"{srv.base_url}/health"
            resultado = self.mod.verify(cfg)
        self.assertFalse(resultado["ok"])
        self.assertEqual(len(resultado["desfase"]), 1)
        remedio = resultado["desfase"][0]["remedio"]
        self.assertIn("build_view", remedio)
        self.assertIn("kwipu-bridge", remedio)
        self.assertIn("kwipu-mcp", remedio)
        self.assertNotIn("subprocess", remedio.lower())

    def test_verify_sin_manifest_previo_no_es_ok_es_nunca_sincronizado(self):
        """gap 87: manifiesto ausente/vacio ya NO es un `ok: True` trivial (falso positivo) —
        nunca se publico nada, asi que `verify` lo declara explicitamente."""
        cfg = {"export_dir": self.export_dir,
                "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}
        resultado = self.mod.verify(cfg)
        self.assertFalse(resultado["ok"])
        self.assertEqual(resultado["desfase"], [])
        self.assertEqual(resultado["razon"], "nunca_sincronizado")

    def test_verify_sin_red_nunca_lanza_y_reporta_desfase(self):
        entradas = [_entrada(id_="mr.pattern.x", cuerpo="x")]
        cfg = {"export_dir": self.export_dir,
                "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}
        self.mod.apply(self.mod.plan(entradas, cfg), cfg)
        resultado = self.mod.verify(cfg)
        self.assertFalse(resultado["ok"])
        self.assertTrue(resultado["desfase"])


class TestMarkdownExportFix1(unittest.TestCase):
    """Fase 3, intento 1, fix1 (2026-09-18): gaps 82/88/89/92/93/96/97/101/102/103."""

    def setUp(self):
        self.mod = _cargar()
        self.tmp = tempfile.mkdtemp(prefix="ks-export-fix1-")
        self.root = os.path.join(self.tmp, "proyecto")
        os.makedirs(self.root, exist_ok=True)
        self.export_dir_rel = "kwipu-export"
        self.cfg = {"export_dir": self.export_dir_rel, "_root": self.root,
                    "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- gap 88/102: export_dir resuelto contra _root, nunca CWD; contencion ----

    def test_export_dir_relativo_se_resuelve_contra_root_no_cwd(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        esperado = os.path.join(self.root, self.export_dir_rel, "mr.pattern.a.md")
        self.assertTrue(os.path.isfile(esperado))

    def test_export_dir_igual_a_root_es_config_invalida(self):
        cfg = dict(self.cfg, export_dir=".")
        with self.assertRaises(self.mod.ConfigInvalida):
            self.mod.plan([], cfg)

    def test_export_dir_dentro_de_approved_es_config_invalida(self):
        cfg = dict(self.cfg, export_dir=os.path.join("docs", "knowledge", "approved", "x"))
        with self.assertRaises(self.mod.ConfigInvalida):
            self.mod.plan([], cfg)

    # ---- gap 89: timeout_ms invalido cae al default en vez de reventar ----

    def test_timeout_ms_no_numerico_cae_al_default(self):
        salud = self.mod.health({"health": {"url": "http://127.0.0.1:1/health",
                                             "timeout_ms": "no-es-un-numero"}})
        self.assertEqual(salud["estado"], "off")  # no lanzo TypeError, siguio y fallo de red

    def test_timeout_ms_none_cae_al_default(self):
        salud = self.mod.health({"health": {"url": "http://127.0.0.1:1/health",
                                             "timeout_ms": None}})
        self.assertEqual(salud["estado"], "off")

    # ---- gap 97: host allowlist (CWE-918) ----

    def test_health_rechaza_host_publico_sin_abrir_conexion(self):
        salud = self.mod.health({"health": {"url": "http://example.com/health", "timeout_ms": 100}})
        self.assertEqual(salud["estado"], "error")
        self.assertIn("no local", salud["detalle"])

    def test_health_rechaza_esquema_file(self):
        salud = self.mod.health({"health": {"url": "file:///etc/passwd", "timeout_ms": 100}})
        self.assertEqual(salud["estado"], "error")

    def test_health_permite_127_0_0_1(self):
        salud = self.mod.health({"health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}})
        self.assertEqual(salud["estado"], "off")  # llego a intentar conectar (rechazo de conexion)

    # ---- gap 93: plan compara hash, sin_cambios si no cambio ----

    def test_plan_reporta_sin_cambios_si_el_hash_no_cambio(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ops2 = self.mod.plan(entradas, self.cfg)
        acciones = {op["knowledge_id"]: op["accion"] for op in ops2}
        self.assertEqual(acciones["mr.pattern.a"], "sin_cambios")

    def test_apply_no_reescribe_fichero_sin_cambios(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ruta = os.path.join(self.root, self.export_dir_rel, "mr.pattern.a.md")
        mtime_1 = os.path.getmtime(ruta)
        resultado = self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        self.assertEqual(resultado["escritos"], 0)
        self.assertEqual(resultado["sin_cambios"], 1)
        self.assertEqual(os.path.getmtime(ruta), mtime_1)

    # ---- gap 82: atomicidad -- un fallo a medias no toca la publicacion anterior ----

    def test_apply_con_id_invalido_a_medias_no_toca_lo_ya_publicado(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ruta_a = os.path.join(self.root, self.export_dir_rel, "mr.pattern.a.md")
        with open(ruta_a, "r", encoding="utf-8") as f:
            contenido_previo = f.read()
        ops_mixtas = [
            {"accion": "upsert", "knowledge_id": "mr.pattern.b", "project": "mr",
             "category": "PATTERN", "version": 1, "confidence": "medium", "cuerpo": "x", "hash": "h"},
            {"accion": "upsert", "knowledge_id": "../escape", "project": "mr",
             "category": "PATTERN", "version": 1, "confidence": "medium", "cuerpo": "x", "hash": "h"},
        ]
        with self.assertRaises(self.mod.ConfigInvalida):
            self.mod.apply(ops_mixtas, self.cfg)
        # la entrada 'a' (publicada antes) sigue intacta, byte a byte
        with open(ruta_a, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), contenido_previo)
        # 'b' (parte de la tanda fallida) NUNCA se publico
        self.assertFalse(os.path.exists(
            os.path.join(self.root, self.export_dir_rel, "mr.pattern.b.md")))
        # no queda directorio de staging huerfano
        restos = [d for d in os.listdir(os.path.join(self.root, self.export_dir_rel))
                  if d.startswith(".staging-")]
        self.assertEqual(restos, [])

    # ---- gap 96: defensa en profundidad en el adaptador (ademas de knowledge-index.py) ----

    def test_apply_rechaza_knowledge_id_con_escape_de_ruta(self):
        ops = [{"accion": "upsert", "knowledge_id": "../../escape", "project": "mr",
                "category": "PATTERN", "version": 1, "confidence": "medium",
                "cuerpo": "x", "hash": "h"}]
        with self.assertRaises(self.mod.ConfigInvalida):
            self.mod.apply(ops, self.cfg)

    # ---- gap 103: _base_url_snapshot preserva query/prefijo y tolera barra final ----

    # ---- gap 83: modo "resumen" = primer parrafo, nunca el cuerpo completo ----

    def test_modo_resumen_solo_publica_el_primer_parrafo(self):
        entradas = [_entrada(id_="mr.pattern.a",
                              cuerpo="Primer parrafo con la idea clave.\n\nSegundo parrafo largo "
                                     "que no deberia salir en el resumen.\n")]
        entradas[0]["modo"] = "resumen"
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ruta = os.path.join(self.root, self.export_dir_rel, "mr.pattern.a.md")
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("Primer parrafo con la idea clave.", texto)
        self.assertNotIn("Segundo parrafo largo", texto)

    def test_modo_resumen_respeta_el_campo_resumen_explicito(self):
        entradas = [_entrada(id_="mr.pattern.a", cuerpo="Cuerpo completo irrelevante aqui.\n")]
        entradas[0]["modo"] = "resumen"
        entradas[0]["resumen"] = "Resumen escrito a mano por el curator."
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ruta = os.path.join(self.root, self.export_dir_rel, "mr.pattern.a.md")
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("Resumen escrito a mano por el curator.", texto)
        self.assertNotIn("Cuerpo completo irrelevante", texto)

    def test_modo_completo_publica_el_cuerpo_entero(self):
        entradas = [_entrada(id_="mr.pattern.a",
                              cuerpo="Primer parrafo.\n\nSegundo parrafo tambien presente.\n")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ruta = os.path.join(self.root, self.export_dir_rel, "mr.pattern.a.md")
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
        self.assertIn("Segundo parrafo tambien presente.", texto)

    def test_base_url_snapshot_con_query_y_barra_final(self):
        self.assertEqual(
            self.mod._base_url_snapshot("http://127.0.0.1:8765/api/health/"),
            "http://127.0.0.1:8765/api")
        self.assertEqual(
            self.mod._base_url_snapshot("http://127.0.0.1:8765/health"),
            "http://127.0.0.1:8765")


class TestMarkdownExportVerifyHash(unittest.TestCase):
    """gap 101: verify() compara hash cuando el snapshot lo trae, y lo declara si no."""

    def setUp(self):
        self.mod = _cargar()
        self.tmp = tempfile.mkdtemp(prefix="ks-export-verifyhash-")
        self.export_dir = os.path.join(self.tmp, "kwipu-export")
        self.cfg = {"export_dir": self.export_dir,
                    "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_verify_declara_comparacion_por_nombre_si_snapshot_no_trae_hash(self):
        entradas = [_entrada(id_="mr.pattern.readme", cuerpo="x")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        os.replace(os.path.join(self.export_dir, "mr.pattern.readme.md"),
                   os.path.join(self.export_dir, "README.md"))
        manifest_path = os.path.join(self.export_dir, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
        m["entries"]["mr.pattern.readme"]["ruta_relativa"] = "README.md"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        cuerpo = _leer_fixture("kwipu-graph-snapshot-2026-09-18.json").encode("utf-8")
        with _ServidorFixturasContext({"/graph/snapshot": (200, cuerpo)}) as srv:
            self.cfg["health"]["url"] = f"{srv.base_url}/health"
            resultado = self.mod.verify(self.cfg)
        self.assertEqual(resultado["comparacion"], "nombre")

    def test_verify_detecta_desfase_por_hash_distinto_aunque_el_nombre_coincida(self):
        entradas = [_entrada(id_="mr.pattern.readme", cuerpo="x")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        os.replace(os.path.join(self.export_dir, "mr.pattern.readme.md"),
                   os.path.join(self.export_dir, "README.md"))
        manifest_path = os.path.join(self.export_dir, "manifest.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
        m["entries"]["mr.pattern.readme"]["ruta_relativa"] = "README.md"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(m, f)
        snapshot = json.loads(_leer_fixture("kwipu-graph-snapshot-2026-09-18.json"))
        for nodo in snapshot.get("nodes", []):
            if isinstance(nodo, dict) and nodo.get("file_name") == "README.md":
                nodo["hash"] = "hash-distinto-de-mentira"
        cuerpo = json.dumps(snapshot).encode("utf-8")
        with _ServidorFixturasContext({"/graph/snapshot": (200, cuerpo)}) as srv:
            self.cfg["health"]["url"] = f"{srv.base_url}/health"
            resultado = self.mod.verify(self.cfg)
        self.assertFalse(resultado["ok"])
        self.assertEqual(resultado["comparacion"], "hash")


class TestMarkdownExportFix2(unittest.TestCase):
    """Fase 3, intento 2, fix2 (2026-09-18): gaps 109/112/115/117/121/125 - publicacion por
    intercambio de directorio, revalidacion de host en redirecciones, DNS con tope, contencion
    con realpath/normcase, ops sin_cambios sin cuerpo."""

    def setUp(self):
        self.mod = _cargar()
        self.tmp = tempfile.mkdtemp(prefix="ks-export-fix2-")
        self.root = os.path.join(self.tmp, "proyecto")
        os.makedirs(self.root, exist_ok=True)
        self.export_dir_rel = "kwipu-export"
        self.cfg = {"export_dir": self.export_dir_rel, "_root": self.root,
                    "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- gap 115: el staging es HERMANO de export_dir, nunca un hijo ----

    def test_apply_no_deja_staging_dentro_de_export_dir(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        export_dir = os.path.join(self.root, self.export_dir_rel)
        hijos = os.listdir(export_dir)
        self.assertFalse(any(h.startswith(".staging-") for h in hijos))
        padre = os.path.dirname(export_dir)
        hermanos_staging = [h for h in os.listdir(padre)
                             if h.startswith(os.path.basename(export_dir) + ".staging-")]
        self.assertEqual(hermanos_staging, [])

    def test_lock_es_fichero_hermano_no_hijo(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        export_dir = os.path.join(self.root, self.export_dir_rel)
        self.assertFalse(os.path.exists(os.path.join(export_dir, ".knowledge-services.lock")))
        self.assertFalse(os.path.exists(export_dir + ".lock"))  # se libera al salir del `with`

    # ---- gap 82/115: reparacion de una corrida interrumpida (.prev huerfano) ----

    def test_apply_repone_prev_huerfano_si_export_dir_desaparecio(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        export_dir = os.path.join(self.root, self.export_dir_rel)
        prev_dir = export_dir + ".prev"
        os.replace(export_dir, prev_dir)  # simula: primer rename hecho, proceso murio ahi
        self.assertFalse(os.path.isdir(export_dir))
        # `plan()` se calcula ANTES de que `apply()` repare `.prev` (no ve manifest.json todavia,
        # asi que pide `upsert`); la reparacion ocurre dentro de `apply()`, bajo el lock, y el
        # resultado es el mismo contenido publicado de nuevo (idempotente en contenido, aunque no
        # literalmente "sin_cambios" para esta pasada).
        resultado = self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        self.assertTrue(os.path.isdir(export_dir))
        self.assertFalse(os.path.isdir(prev_dir))
        self.assertEqual(resultado["escritos"], 1)

    def test_apply_purga_staging_huerfano_viejo(self):
        export_dir = os.path.join(self.root, self.export_dir_rel)
        os.makedirs(export_dir, exist_ok=True)
        staging_viejo = export_dir + ".staging-999999"
        os.makedirs(staging_viejo, exist_ok=True)
        viejo = 1  # epoch bajo -> edad enorme
        os.utime(staging_viejo, (viejo, viejo))
        self.mod.apply(self.mod.plan([], self.cfg), self.cfg)
        self.assertFalse(os.path.isdir(staging_viejo))

    # ---- gap 109: rebuild regenera un fichero publicado que se borro a mano ----

    def test_rebuild_regenera_fichero_borrado_a_mano(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ruta = os.path.join(self.root, self.export_dir_rel, "mr.pattern.a.md")
        os.remove(ruta)
        self.assertFalse(os.path.isfile(ruta))
        resultado = self.mod.rebuild(entradas, self.cfg)
        self.assertTrue(os.path.isfile(ruta))
        self.assertEqual(resultado["escritos"], 1)

    def test_plan_marca_upsert_si_el_fichero_publicado_ya_no_existe(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ruta = os.path.join(self.root, self.export_dir_rel, "mr.pattern.a.md")
        os.remove(ruta)
        ops = self.mod.plan(entradas, self.cfg)
        acciones = {op["knowledge_id"]: op["accion"] for op in ops}
        self.assertEqual(acciones["mr.pattern.a"], "upsert")

    def test_rebuild_descarta_huerfanos_no_presentes_en_entries(self):
        entradas = [_entrada(id_="mr.pattern.a"), _entrada(id_="mr.pattern.b")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        self.mod.rebuild([_entrada(id_="mr.pattern.a")], self.cfg)
        export_dir = os.path.join(self.root, self.export_dir_rel)
        self.assertTrue(os.path.isfile(os.path.join(export_dir, "mr.pattern.a.md")))
        self.assertFalse(os.path.isfile(os.path.join(export_dir, "mr.pattern.b.md")))

    # ---- gap 125: los ops sin_cambios no cargan "cuerpo" ----

    def test_plan_sin_cambios_no_lleva_cuerpo(self):
        entradas = [_entrada(id_="mr.pattern.a")]
        self.mod.apply(self.mod.plan(entradas, self.cfg), self.cfg)
        ops2 = self.mod.plan(entradas, self.cfg)
        op_sin_cambios = next(op for op in ops2 if op["knowledge_id"] == "mr.pattern.a")
        self.assertEqual(op_sin_cambios["accion"], "sin_cambios")
        self.assertNotIn("cuerpo", op_sin_cambios)

    # ---- gap 112: redireccion HTTP a host publico se rechaza sin seguirla ----

    def test_health_rechaza_redireccion_a_host_publico(self):
        class _HandlerRedirect(_ServidorFixturas):
            def _responder(self):
                if self.path == "/health":
                    self.send_response(302)
                    self.send_header("Location", "http://example.com/health")
                    self.end_headers()
                else:
                    super()._responder()

        httpd = HTTPServer(("127.0.0.1", 0), _HandlerRedirect)
        puerto = httpd.server_address[1]
        hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
        hilo.start()
        try:
            salud = self.mod.health(
                {"health": {"url": f"http://127.0.0.1:{puerto}/health", "timeout_ms": 500}})
            self.assertEqual(salud["estado"], "error")
            self.assertIn("no local", salud["detalle"])
        finally:
            httpd.shutdown()
            httpd.server_close()

    def test_health_sigue_redireccion_a_host_local(self):
        fixture = _leer_fixture("kwipu-health-2026-09-18.json")

        class _HandlerRedirectLocal(_ServidorFixturas):
            def _responder(self):
                if self.path == "/health":
                    self.send_response(302)
                    loc = f"http://127.0.0.1:{self.server.server_address[1]}/health2"
                    self.send_header("Location", loc)
                    self.end_headers()
                elif self.path == "/health2":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(fixture.encode("utf-8"))
                else:
                    super()._responder()

        httpd = HTTPServer(("127.0.0.1", 0), _HandlerRedirectLocal)
        puerto = httpd.server_address[1]
        hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
        hilo.start()
        try:
            salud = self.mod.health(
                {"health": {"url": f"http://127.0.0.1:{puerto}/health", "timeout_ms": 500}})
            self.assertIn(salud["estado"], ("sano", "degradado"))
        finally:
            httpd.shutdown()
            httpd.server_close()

    # ---- gap 117: la resolucion DNS respeta un tope y se cachea ----

    def test_host_permitido_dns_lento_no_bloquea_mas_del_tope(self):
        import time as _time
        self.mod._dns_cache.clear()
        original = self.mod.socket.gethostbyname

        def _lento(host):
            _time.sleep(5)
            return "8.8.8.8"

        self.mod.socket.gethostbyname = _lento
        try:
            t0 = _time.monotonic()
            permitido = self.mod._host_permitido("http://dns-lento.ejemplo.invalid/x")
            duracion = _time.monotonic() - t0
        finally:
            self.mod.socket.gethostbyname = original
        self.assertFalse(permitido)
        self.assertLess(duracion, 2.0)

    def test_host_permitido_cachea_resolucion_por_proceso(self):
        self.mod._dns_cache.clear()
        llamadas = []
        original = self.mod.socket.gethostbyname

        def _contador(host):
            llamadas.append(host)
            return "127.0.0.1"

        self.mod.socket.gethostbyname = _contador
        try:
            self.mod._host_permitido("http://cacheado.ejemplo.invalid/a")
            self.mod._host_permitido("http://cacheado.ejemplo.invalid/b")
        finally:
            self.mod.socket.gethostbyname = original
        self.assertEqual(len(llamadas), 1)

    # ---- gap 121: contencion con realpath/normcase (junction o mayusculas) ----

    def test_export_dir_dentro_de_approved_con_mayusculas_distintas_es_config_invalida(self):
        cfg = dict(self.cfg, export_dir=os.path.join(
            "Docs", "Knowledge", "Approved", "x").upper())
        with self.assertRaises(self.mod.ConfigInvalida):
            self.mod.plan([], cfg)

    def test_export_dir_por_symlink_hacia_approved_es_config_invalida(self):
        approved = os.path.join(self.root, "docs", "knowledge", "approved")
        os.makedirs(approved, exist_ok=True)
        enlace = os.path.join(self.root, "enlace-a-approved")
        try:
            os.symlink(approved, enlace, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks no disponibles en este entorno (permiso/plataforma)")
        cfg = dict(self.cfg, export_dir=enlace)
        with self.assertRaises(self.mod.ConfigInvalida):
            self.mod.plan([], cfg)


if __name__ == "__main__":
    unittest.main()
