#!/usr/bin/env python3
"""Tests de openapi-lint.py (skill `api-contract`, superiority T-05). Ejecutar: pytest -q
skills/api-contract/scripts

Funciones (`validar`/`diff_specs`/`parse_yaml_simple`) importadas directamente para los casos de
estructura; `run()` (subprocess) para el contrato de exit codes de la CLI. El fallback YAML se
prueba llamando a `parse_yaml_simple` directamente Y forzando `ImportError` de `yaml` con
`sys.modules` (el sandbox de CI puede tener PyYAML instalado o no: ambas rutas deben probarse sin
depender de qué haya en el entorno)."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "openapi-lint.py")

spec = importlib.util.spec_from_file_location("openapi_lint", SCRIPT)
oal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(oal)


def run(*args):
    r = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def write(tmpdir, rel, text):
    p = os.path.join(tmpdir, rel)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return p


def write_json(tmpdir, rel, obj):
    return write(tmpdir, rel, json.dumps(obj))


# ---------------------------------------------------------------- fixtures compartidas ----

def spec_valida():
    return {
        "openapi": "3.0.3",
        "info": {"title": "Demo", "version": "1.0.0"},
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "listPets",
                    "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}],
                    "responses": {
                        "200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/PetList"}}}},
                        "400": {"description": "bad"},
                    },
                },
                "post": {
                    "operationId": "createPet",
                    "requestBody": {"content": {"application/json": {
                        "schema": {"type": "object", "additionalProperties": False}}}},
                    "responses": {
                        "201": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}}},
                        "422": {"description": "invalid"},
                    },
                },
            }
        },
        "components": {"schemas": {
            "Pet": {"type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"}}},
            "PetList": {"type": "array", "items": {"$ref": "#/components/schemas/Pet"}},
        }},
    }


# ================================================================================ validar ====

def test_spec_valida_sin_errores():
    errores, avisos = oal.validar(spec_valida())
    assert errores == [] and avisos == []


def test_falta_operation_id():
    s = spec_valida()
    del s["paths"]["/pets"]["get"]["operationId"]
    errores, _ = oal.validar(s)
    assert any("operationId" in e["mensaje"] for e in errores)


def test_operation_id_duplicado():
    s = spec_valida()
    s["paths"]["/pets"]["post"]["operationId"] = "listPets"
    errores, _ = oal.validar(s)
    assert any("duplicado" in e["mensaje"] for e in errores)


def test_sin_respuesta_4xx_5xx():
    s = spec_valida()
    s["paths"]["/pets"]["get"]["responses"] = {"200": {"description": "ok"}}
    errores, _ = oal.validar(s)
    assert any("4xx/5xx" in e["mensaje"] for e in errores)


def test_sin_respuesta_2xx():
    s = spec_valida()
    s["paths"]["/pets"]["get"]["responses"] = {"400": {"description": "bad"}}
    errores, _ = oal.validar(s)
    assert any("2xx" in e["mensaje"] for e in errores)


def test_ref_roto():
    s = spec_valida()
    s["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"] = \
        "#/components/schemas/NoExiste"
    errores, _ = oal.validar(s)
    assert any("$ref` roto" in e["mensaje"] for e in errores)


def test_parametro_sin_schema_ni_content():
    s = spec_valida()
    s["paths"]["/pets"]["get"]["parameters"] = [{"name": "limit", "in": "query"}]
    errores, _ = oal.validar(s)
    assert any("sin `schema` ni `content`" in e["mensaje"] for e in errores)


def test_paths_vacio_es_error():
    s = spec_valida()
    s["paths"] = {}
    errores, _ = oal.validar(s)
    assert any("paths" in e["ruta"] for e in errores)


def test_openapi_no_es_3x():
    s = spec_valida()
    s["openapi"] = "2.0"
    errores, _ = oal.validar(s)
    assert any(e["ruta"] == "/openapi" for e in errores)


def test_request_body_objeto_sin_additional_properties_es_aviso_no_error():
    s = spec_valida()
    s["paths"]["/pets"]["post"]["requestBody"] = {"content": {"application/json": {"schema": {"type": "object"}}}}
    errores, avisos = oal.validar(s)
    assert errores == []
    assert any("additionalProperties" in a["mensaje"] for a in avisos)


# ============================================================== parser YAML sin dependencias ====

YAML_TEXTO = """openapi: 3.0.3
info:
  title: Demo
  version: 1.0.0
paths:
  /pets:
    get:
      operationId: listPets
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
        - name: tags
          in: query
          schema:
            type: array
      responses:
        '200':
          description: ok
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PetList'
        '400':
          description: bad
components:
  schemas:
    Pet:
      type: object
      properties:
        id:
          type: string
        status:
          type: string
          enum: [available, pending, sold]
    PetList:
      type: array
      items:
        $ref: '#/components/schemas/Pet'
"""


def test_yaml_fallback_coincide_con_pyyaml():
    """El parser interno debe producir EXACTAMENTE la misma estructura que PyYAML para el
    subconjunto habitual de una spec OpenAPI (mapas/listas anidados, `$ref` entrecomillado, flow list)."""
    pytest_module = None
    try:
        import yaml
    except ImportError:
        return  # sin PyYAML instalado no hay referencia contra la que comparar; no falla el test
    via_interno = oal.parse_yaml_simple(YAML_TEXTO)
    via_pyyaml = yaml.safe_load(YAML_TEXTO)
    assert via_interno == via_pyyaml
    errores, avisos = oal.validar(via_interno)
    assert errores == [] and avisos == []


def test_yaml_fallback_se_usa_sin_pyyaml():
    """Fuerza `ImportError` de `yaml` (sys.modules) para probar la rama de `cargar_documento` que
    NO depende de si el sandbox tiene PyYAML instalado."""
    with tempfile.TemporaryDirectory() as d:
        p = write(d, "spec.yaml", YAML_TEXTO)
        with mock.patch.dict(sys.modules, {"yaml": None}):
            doc, err = oal.cargar_documento(p)
        assert err is None
        assert doc["openapi"] == "3.0.3"
        errores, _ = oal.validar(doc)
        assert errores == []


def test_yaml_fallback_rechaza_bloque_escalar():
    texto = "openapi: 3.0.3\ndescripcion: |\n  varias\n  lineas\n"
    try:
        oal.parse_yaml_simple(texto)
        assert False, "debía lanzar YamlSimpleError"
    except oal.YamlSimpleError as e:
        assert "|" in str(e) or "bloque" in str(e)


def test_yaml_fallback_sin_pyyaml_con_sintaxis_exotica_da_exit_2_con_aviso_instalar_pyyaml():
    with tempfile.TemporaryDirectory() as d:
        p = write(d, "raro.yaml", "openapi: 3.0.3\ndescripcion: |\n  bloque\n")
        with mock.patch.dict(sys.modules, {"yaml": None}):
            doc, err = oal.cargar_documento(p)
        assert doc is None
        assert "PyYAML" in err


def test_yaml_fallback_colecciones_flow():
    assert oal.parse_yaml_simple("x: [1, 2, 3]\n") == {"x": [1, 2, 3]}
    assert oal.parse_yaml_simple('x: {a: 1, b: "dos"}\n') == {"x": {"a": 1, "b": "dos"}}
    assert oal.parse_yaml_simple("x: [a, 'b c', true, null]\n") == {"x": ["a", "b c", True, None]}


# ============================================================================ diff / --diff ====

def spec_base_diff():
    return {"openapi": "3.0.3", "paths": {
        "/pets": {"get": {
            "operationId": "listPets",
            "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}],
            "responses": {"200": {"content": {"application/json": {"schema": {
                "type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}}}},
                          "400": {"description": "bad"}},
        }},
        "/legacy": {"get": {"operationId": "legacyOp", "responses": {"200": {"description": "ok"}, "400": {"description": "bad"}}}},
    }}


def test_diff_path_eliminado_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    del new["paths"]["/legacy"]
    cambios = oal.diff_specs(old, new)
    c = [c for c in cambios if "path eliminado" in c["mensaje"]]
    assert len(c) == 1 and c[0]["rompedor"] is True


def test_diff_path_nuevo_es_informativo():
    old, new = spec_base_diff(), spec_base_diff()
    new["paths"]["/new"] = {"get": {"operationId": "newOp", "responses": {"200": {"description": "ok"}, "400": {"description": "bad"}}}}
    cambios = oal.diff_specs(old, new)
    c = [c for c in cambios if "path nuevo" in c["mensaje"]]
    assert len(c) == 1 and c[0]["rompedor"] is False


def test_diff_operacion_eliminada_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    del new["paths"]["/legacy"]["get"]
    new["paths"]["/legacy"] = {}
    cambios = oal.diff_specs(old, new)
    assert any("operación eliminada" in c["mensaje"] and c["rompedor"] for c in cambios)


def test_diff_parametro_obligatorio_nuevo_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    new["paths"]["/pets"]["get"]["parameters"].append(
        {"name": "apiKey", "in": "query", "required": True, "schema": {"type": "string"}})
    cambios = oal.diff_specs(old, new)
    c = [c for c in cambios if "apiKey" in c["mensaje"]]
    assert len(c) == 1 and c[0]["rompedor"] is True and "obligatorio nuevo" in c[0]["mensaje"]


def test_diff_parametro_opcional_nuevo_es_informativo():
    old, new = spec_base_diff(), spec_base_diff()
    new["paths"]["/pets"]["get"]["parameters"].append({"name": "q", "in": "query", "schema": {"type": "string"}})
    cambios = oal.diff_specs(old, new)
    c = [c for c in cambios if "q" == c["ruta"].rsplit("/", 1)[-1]]
    assert len(c) == 1 and c[0]["rompedor"] is False


def test_diff_parametro_pasa_a_obligatorio_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    new["paths"]["/pets"]["get"]["parameters"][0]["required"] = True
    cambios = oal.diff_specs(old, new)
    assert any("pasa a obligatorio" in c["mensaje"] and c["rompedor"] for c in cambios)


def test_diff_parametro_eliminado_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    new["paths"]["/pets"]["get"]["parameters"] = []
    cambios = oal.diff_specs(old, new)
    assert any("parámetro eliminado" in c["mensaje"] and c["rompedor"] for c in cambios)


def test_diff_tipo_cambiado_en_parametro_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    new["paths"]["/pets"]["get"]["parameters"][0]["schema"]["type"] = "string"
    cambios = oal.diff_specs(old, new)
    assert any("tipo cambiado en parámetro" in c["mensaje"] and c["rompedor"] for c in cambios)


def test_diff_campo_de_respuesta_eliminado_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    del new["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["name"]
    cambios = oal.diff_specs(old, new)
    assert any("campo de respuesta eliminado: name" in c["mensaje"] and c["rompedor"] for c in cambios)


def test_diff_campo_de_respuesta_nuevo_es_informativo():
    old, new = spec_base_diff(), spec_base_diff()
    new["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["extra"] = {"type": "string"}
    cambios = oal.diff_specs(old, new)
    c = [c for c in cambios if "extra" in c["mensaje"]]
    assert len(c) == 1 and c[0]["rompedor"] is False


def test_diff_tipo_cambiado_en_campo_de_respuesta_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    new["paths"]["/pets"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["properties"]["id"]["type"] = "integer"
    cambios = oal.diff_specs(old, new)
    assert any("tipo cambiado en campo id" in c["mensaje"] and c["rompedor"] for c in cambios)


def test_diff_enum_pierde_valores_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    old["paths"]["/pets"]["get"]["parameters"][0]["schema"]["enum"] = ["a", "b", "c"]
    new["paths"]["/pets"]["get"]["parameters"][0]["schema"]["enum"] = ["a", "b"]
    cambios = oal.diff_specs(old, new)
    assert any("enum" in c["mensaje"] and c["rompedor"] for c in cambios)


def test_diff_enum_que_solo_anade_valores_no_es_rompedor():
    old, new = spec_base_diff(), spec_base_diff()
    old["paths"]["/pets"]["get"]["parameters"][0]["schema"]["enum"] = ["a", "b"]
    new["paths"]["/pets"]["get"]["parameters"][0]["schema"]["enum"] = ["a", "b", "c"]
    cambios = oal.diff_specs(old, new)
    assert not any("enum" in c["mensaje"] for c in cambios)


def test_diff_ref_en_respuesta_se_resuelve_para_comparar_propiedades():
    old = {"openapi": "3.0.3", "paths": {"/pets": {"get": {"operationId": "listPets", "responses": {
        "200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}}}, "400": {}}}}},
        "components": {"schemas": {"Pet": {"type": "object", "properties": {"id": {"type": "string"}, "name": {"type": "string"}}}}}}
    new = {"openapi": "3.0.3", "paths": {"/pets": {"get": {"operationId": "listPets", "responses": {
        "200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Pet"}}}}, "400": {}}}}},
        "components": {"schemas": {"Pet": {"type": "object", "properties": {"id": {"type": "string"}}}}}}
    cambios = oal.diff_specs(old, new)
    assert any("campo de respuesta eliminado: name" in c["mensaje"] for c in cambios)


def test_diff_sin_cambios_da_lista_vacia():
    s = spec_base_diff()
    assert oal.diff_specs(s, spec_base_diff()) == []


# ================================================================================ CLI ====

def test_cli_spec_valida_exit_0():
    with tempfile.TemporaryDirectory() as d:
        p = write_json(d, "v.json", spec_valida())
        code, out, err = run(p)
        assert code == 0 and "VÁLIDA" in out


def test_cli_spec_invalida_exit_1_con_errores_listados():
    with tempfile.TemporaryDirectory() as d:
        s = spec_valida()
        del s["paths"]["/pets"]["get"]["operationId"]
        p = write_json(d, "v.json", s)
        code, out, err = run(p)
        assert code == 1 and "operationId" in out


def test_cli_diff_rompedor_exit_1():
    with tempfile.TemporaryDirectory() as d:
        old, new = spec_base_diff(), spec_base_diff()
        del new["paths"]["/legacy"]
        po, pn = write_json(d, "old.json", old), write_json(d, "new.json", new)
        code, out, err = run("--diff", po, pn)
        assert code == 1 and "ROMPEDOR" in out


def test_cli_diff_compatible_exit_0():
    with tempfile.TemporaryDirectory() as d:
        old, new = spec_base_diff(), spec_base_diff()
        new["paths"]["/new"] = {"get": {"operationId": "newOp", "responses": {"200": {"description": "ok"}, "400": {}}}}
        po, pn = write_json(d, "old.json", old), write_json(d, "new.json", new)
        code, out, err = run("--diff", po, pn)
        assert code == 0 and "sin cambios" not in out


def test_cli_fichero_inexistente_exit_2():
    code, out, err = run("/no/existe/spec.json")
    assert code == 2 and "no existe" in out


def test_cli_sin_argumentos_exit_2():
    code, out, err = run()
    assert code == 2 and "uso" in err


def test_cli_json_y_md_coherentes():
    with tempfile.TemporaryDirectory() as d:
        s = spec_valida()
        del s["paths"]["/pets"]["get"]["operationId"]
        p = write_json(d, "v.json", s)
        code_md, out_md, _ = run(p)
        code_json, out_json, _ = run(p, "--json")
        data = json.loads(out_json)
        assert code_md == code_json == data["exit"] == 1
        assert len(data["errores"]) >= 1
        assert "operationId" in out_md
