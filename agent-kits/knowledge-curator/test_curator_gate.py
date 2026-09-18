import importlib.util
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    spec = importlib.util.spec_from_file_location("curator_gate", os.path.join(HERE, "curator-gate.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["curator_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


cg = _load()

TAXONOMY_DEFAULT_CATEGORIAS = {"DECISION", "PATTERN", "GOTCHA", "LESSON"}  # plantilla del plugin


def _escribir(tmp, nombre, contenido):
    ruta = os.path.join(tmp, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta


CANDIDATO_COMPLETO = """---
id: ca.gotcha.ejemplo
category: GOTCHA
evidencia: validated_case
fuentes:
  - docs/x.md
tags:
  - area:testing
---

# Un gotcha de ejemplo
"""

CANDIDATO_SIN_EVIDENCIA = """---
id: ca.gotcha.ejemplo
category: GOTCHA
fuentes:
  - docs/x.md
tags:
  - area:testing
---

# Sin evidencia
"""

CANDIDATO_EVIDENCIA_INSUFICIENTE = """---
id: ca.pattern.ejemplo
category: PATTERN
evidencia: observation
fuentes:
  - docs/x.md
tags:
  - area:testing
---

# PATTERN exige multiple_validated_cases; observation es el nivel mas bajo
"""

CANDIDATO_SIN_FUENTES_NI_TAGS = """---
id: ca.gotcha.ejemplo
category: GOTCHA
evidencia: validated_case
---

# Sin fuentes ni tags
"""

CANDIDATO_ESTADO_APPROVED_INVALIDO = """---
id: ca.gotcha.ejemplo
category: GOTCHA
evidencia: validated_case
fuentes:
  - docs/x.md
tags:
  - area:testing
estado: approved
---

# `estado: approved` no es el token reservado (gap 34: es `aprobado`)
"""

CANDIDATO_DENYLIST = """---
id: ca.gotcha.ejemplo
category: GOTCHA
evidencia: validated_case
fuentes:
  - docs/x.md
tags:
  - area:testing
---

# Nota

Esto es basicamente un resumen de chain-of-thought del agente, sin mas.
"""

CANDIDATO_SIN_CATEGORIA = """---
id: ca.gotcha.ejemplo
evidencia: validated_case
fuentes:
  - docs/x.md
tags:
  - area:testing
---

# Sin categoria declarada
"""


# ------------------------------------------------------------------ approve: caso feliz


def test_approve_candidato_completo_es_permitido():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 0
        assert veredicto["errores"] == []
        assert veredicto["categoria"] == "GOTCHA"


def test_approve_respeta_category_override_sobre_frontmatter():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)  # frontmatter dice GOTCHA
        veredicto, exit_code = cg.evaluar(ruta, "approve", category_override="LESSON", root=tmp)
        # LESSON exige min_evidence single_case; validated_case la supera -> sigue permitido
        assert exit_code == 0
        assert veredicto["categoria"] == "LESSON"


# ------------------------------------------------------------------ approve: bloqueado (gap 3)


def test_approve_sin_evidencia_bloquea():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_SIN_EVIDENCIA)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "evidencia" for e in veredicto["errores"])


def test_approve_evidencia_insuficiente_para_la_categoria_exacta_bloquea():
    """gap 3: PATTERN exige `multiple_validated_cases`; `observation` es el nivel mas bajo."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_EVIDENCIA_INSUFICIENTE)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "evidencia" and "min_evidence" in e["mensaje"] for e in veredicto["errores"])


def test_approve_sin_fuentes_ni_tags_bloquea_ambos():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_SIN_FUENTES_NI_TAGS)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        campos = {e["campo"] for e in veredicto["errores"]}
        assert "fuentes" in campos and "tags" in campos


def test_approve_sin_categoria_es_error_de_uso():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_SIN_CATEGORIA)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 2
        assert any(e["campo"] == "category" for e in veredicto["errores"])


def test_approve_categoria_no_declarada_es_error_de_uso():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)
        veredicto, exit_code = cg.evaluar(ruta, "approve", category_override="NO_EXISTE", root=tmp)
        assert exit_code == 2
        assert any(e["campo"] == "category" for e in veredicto["errores"])


# ------------------------------------------------------------------ gap 34: token de `estado`


def test_approve_estado_approved_en_ingles_bloquea():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_ESTADO_APPROVED_INVALIDO)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "estado" for e in veredicto["errores"])


def test_approve_estado_aprobado_literal_no_bloquea():
    contenido = CANDIDATO_COMPLETO.replace("tags:", "estado: aprobado\ntags:")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 0


# ------------------------------------------------------------------ lista negra


def test_approve_con_termino_de_la_lista_negra_bloquea():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_DENYLIST)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "denylist" for e in veredicto["errores"])


# ------------------------------------------------------------------ reject / needs_changes: sin exigencia


def test_reject_no_exige_evidencia_ni_fuentes():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_SIN_FUENTES_NI_TAGS)
        veredicto, exit_code = cg.evaluar(ruta, "reject", root=tmp)
        assert exit_code == 0
        assert veredicto["errores"] == []


def test_needs_changes_no_exige_evidencia_ni_fuentes():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_SIN_EVIDENCIA)
        veredicto, exit_code = cg.evaluar(ruta, "needs_changes", root=tmp)
        assert exit_code == 0


def test_reject_con_categoria_no_declarada_sigue_siendo_error_de_uso():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)
        veredicto, exit_code = cg.evaluar(ruta, "reject", category_override="NO_EXISTE", root=tmp)
        assert exit_code == 2


# ------------------------------------------------------------------ uso / errores de entrada


def test_decision_invalida_es_error_de_uso():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)
        veredicto, exit_code = cg.evaluar(ruta, "aprobar-ya", root=tmp)
        assert exit_code == 2


def test_candidato_inexistente_es_error_de_uso():
    with tempfile.TemporaryDirectory() as tmp:
        veredicto, exit_code = cg.evaluar(os.path.join(tmp, "no-existe.md"), "approve", root=tmp)
        assert exit_code == 2
        assert veredicto["errores"][0]["campo"] == "$"


# ------------------------------------------------------------------ CLI


def test_cli_json_exit_0(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)
        exit_code = cg.main([ruta, "--decision", "approve", "--root", tmp, "--json"])
        assert exit_code == 0
        salida = json.loads(capsys.readouterr().out)
        assert salida["decision"] == "approve"


def test_cli_texto_exit_1_lista_errores(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_SIN_EVIDENCIA)
        exit_code = cg.main([ruta, "--decision", "approve", "--root", tmp])
        assert exit_code == 1
        assert "evidencia" in capsys.readouterr().out
