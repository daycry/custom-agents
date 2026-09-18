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

    def test_verify_sin_manifest_previo_es_ok_trivial(self):
        cfg = {"export_dir": self.export_dir,
                "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}
        resultado = self.mod.verify(cfg)
        self.assertTrue(resultado["ok"])
        self.assertEqual(resultado["desfase"], [])

    def test_verify_sin_red_nunca_lanza_y_reporta_desfase(self):
        entradas = [_entrada(id_="mr.pattern.x", cuerpo="x")]
        cfg = {"export_dir": self.export_dir,
                "health": {"url": "http://127.0.0.1:1/health", "timeout_ms": 100}}
        self.mod.apply(self.mod.plan(entradas, cfg), cfg)
        resultado = self.mod.verify(cfg)
        self.assertFalse(resultado["ok"])
        self.assertTrue(resultado["desfase"])


if __name__ == "__main__":
    unittest.main()
