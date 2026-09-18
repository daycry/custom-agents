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


def _escribir(tmp, nombre, contenido, carpeta="pending"):
    """Escribe el candidato bajo `<tmp>/docs/knowledge/candidates/<carpeta>/<nombre>` (gap 48):
    la contencion de `curator-gate.py` exige que un candidato viva ahi, asi que las fixtures
    tienen que reflejar el arbol real, no un fichero suelto en la raiz del tmpdir."""
    d = os.path.join(tmp, "docs", "knowledge", "candidates", carpeta)
    os.makedirs(d, exist_ok=True)
    ruta = os.path.join(d, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)
    return ruta


def _taxonomy(tmp, categories, evidence_levels=None, denylist=None):
    """Escribe `<tmp>/.claude/knowledge-services/taxonomy.json` propio del proyecto (gaps 47/50):
    sin `evidence_levels`, `cargar_taxonomia()` sigue devolviendo `origen == "proyecto"` (a
    diferencia de no tener NINGUN fichero, que da `origen == "default"`) — es el caso real que
    ejercita la escalera por defecto del gate cuando el proyecto declara categorias propias pero
    no una escalera de evidencia propia."""
    cfg = {"version": 1, "id_prefix": "ca", "categories": categories}
    if evidence_levels is not None:
        cfg["evidence_levels"] = evidence_levels
    if denylist is not None:
        cfg["denylist"] = denylist
    d = os.path.join(tmp, ".claude", "knowledge-services")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "taxonomy.json"), "w", encoding="utf-8") as f:
        json.dump(cfg, f)


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

# gap 61: `fuentes`/`tags` PRESENTES pero escalares (no lista) — mensaje distinto de "falta".
CANDIDATO_FUENTES_ESCALAR = """---
id: ca.gotcha.ejemplo
category: GOTCHA
evidencia: validated_case
fuentes: docs/x.md
tags:
  - area:testing
---

# `fuentes` declarado pero como escalar, no lista
"""

CANDIDATO_TAGS_ESCALAR = """---
id: ca.gotcha.ejemplo
category: GOTCHA
evidencia: validated_case
fuentes:
  - docs/x.md
tags: area:testing
---

# `tags` declarado pero como escalar, no lista
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


def test_approve_fuentes_ausente_vs_escalar_dan_mensajes_distintos():
    """Gap 61: mismo `campo` (`fuentes`), pero el diagnostico de "falta" y el de "declarado pero
    escalar" tienen que ser mensajes DISTINTOS (gap 52 ya lo exigia para el gate; sin un test que
    compare las dos ramas, un mutante que las colapsa en una sola sigue en verde)."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta_ausente = _escribir(tmp, "ausente.md", CANDIDATO_SIN_FUENTES_NI_TAGS)
        v_ausente, exit_ausente = cg.evaluar(ruta_ausente, "approve", root=tmp)
        ruta_escalar = _escribir(tmp, "escalar.md", CANDIDATO_FUENTES_ESCALAR)
        v_escalar, exit_escalar = cg.evaluar(ruta_escalar, "approve", root=tmp)

        assert exit_ausente == 1 and exit_escalar == 1
        msg_ausente = next(e["mensaje"] for e in v_ausente["errores"] if e["campo"] == "fuentes")
        msg_escalar = next(e["mensaje"] for e in v_escalar["errores"] if e["campo"] == "fuentes")
        assert msg_ausente != msg_escalar
        assert "falta" in msg_ausente and "falta" not in msg_escalar
        assert "declarado" in msg_escalar


def test_approve_tags_ausente_vs_escalar_dan_mensajes_distintos():
    """Gap 61, simetrico para `tags`."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta_ausente = _escribir(tmp, "ausente.md", CANDIDATO_SIN_FUENTES_NI_TAGS)
        v_ausente, exit_ausente = cg.evaluar(ruta_ausente, "approve", root=tmp)
        ruta_escalar = _escribir(tmp, "escalar.md", CANDIDATO_TAGS_ESCALAR)
        v_escalar, exit_escalar = cg.evaluar(ruta_escalar, "approve", root=tmp)

        assert exit_ausente == 1 and exit_escalar == 1
        msg_ausente = next(e["mensaje"] for e in v_ausente["errores"] if e["campo"] == "tags")
        msg_escalar = next(e["mensaje"] for e in v_escalar["errores"] if e["campo"] == "tags")
        assert msg_ausente != msg_escalar
        assert "falta" in msg_ausente and "falta" not in msg_escalar
        assert "declarado" in msg_escalar


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


# ------------------------------------------------------------------ gap 41: lista negra sin falsos positivos


def test_denylist_todo_dos_puntos_dispara_pero_no_la_palabra_todos():
    """Gap 41: el termino de la lista negra es `TODO:` (con los dos puntos), no la palabra
    espanola comun `todos`/`Todos` — `\\b` colisionaba con ambos casos."""
    contenido = CANDIDATO_COMPLETO.replace(
        "# Un gotcha de ejemplo",
        "# Un gotcha de ejemplo\n\nTodos los metodos publicos quedaron probados.")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 0
        assert veredicto["errores"] == []


def test_denylist_todo_dos_puntos_en_el_cuerpo_bloquea():
    contenido = CANDIDATO_COMPLETO.replace(
        "# Un gotcha de ejemplo",
        "# Un gotcha de ejemplo\n\nTODO: limpiar este caso mas adelante.")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "denylist" for e in veredicto["errores"])


def test_denylist_plegado_de_acentos_dispara_sobre_prosa_real():
    """Gap 64: el termino por defecto `conversacion cruda` viaja SIN tildes (ASCII, deliberado),
    pero la prosa real de un candidato SI las lleva — sin plegar acentos, «conversación cruda»
    nunca disparaba."""
    contenido = CANDIDATO_COMPLETO.replace(
        "# Un gotcha de ejemplo",
        "# Un gotcha de ejemplo\n\nEsto es una conversación cruda pegada sin depurar.")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "denylist" for e in veredicto["errores"])


def test_denylist_metodo_con_acento_no_dispara_nada():
    """Gap 64, simetrico: plegar acentos no debe convertir palabras normales en falsos positivos —
    «Método» (con tilde) sigue sin ser el marcador `TODO:` ni ningun otro termino de la lista."""
    contenido = CANDIDATO_COMPLETO.replace(
        "# Un gotcha de ejemplo",
        "# Un gotcha de ejemplo\n\nEl Método public quedó probado end to end.")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 0
        assert veredicto["errores"] == []


def test_denylist_todo_dos_puntos_sin_espacio_dispara():
    """Gap 65: `TODO:limpiar` (sin espacio) tiene que disparar igual que `TODO: limpiar` — un
    termino que ya acaba en puntuacion no debe exigir un caracter "no palabra" tras el, porque el
    propio termino ya aporta el limite."""
    contenido = CANDIDATO_COMPLETO.replace(
        "# Un gotcha de ejemplo",
        "# Un gotcha de ejemplo\n\nTODO:limpiar este caso mas adelante.")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "denylist" for e in veredicto["errores"])


def test_denylist_termino_multipalabra_casa_con_espacios_y_guiones():
    """Gap 66: el termino por defecto `chain-of-thought` (guion) tiene que casar tambien con la
    forma escrita con espacios («chain of thought»), y viceversa."""
    contenido = CANDIDATO_COMPLETO.replace(
        "# Un gotcha de ejemplo",
        "# Un gotcha de ejemplo\n\nEsto es un volcado de chain of thought del agente.")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "denylist" for e in veredicto["errores"])


# ------------------------------------------------------------------ gap 45: degradacion sin kit compartido


def test_kit_compartido_no_disponible_degrada_sin_traceback(monkeypatch):
    """Gap 45: si `agent-kits/shared/` no viaja junto al gate (instalacion parcial), `evaluar()`
    debe devolver un error normal (exit 2), nunca un traceback — y da igual si el que falta es
    `knowledge-schema.py` o `knowledge-index.py` (ambos se cargan en el MISMO `try/except`)."""
    monkeypatch.setattr(cg, "SHARED", os.path.join(tempfile.gettempdir(), "no-existe-de-verdad"))
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 2
        assert veredicto["errores"][0]["campo"] == "$"
        assert "no se encontro" in veredicto["errores"][0]["mensaje"]


def test_kit_compartido_solo_falta_knowledge_index_degrada_sin_traceback(monkeypatch):
    """Gap 70: el test de arriba (gap 45) parchea `SHARED` ENTERO, así que el PRIMER `_cargar`
    (`knowledge-schema.py`) ya falla y la carga de `knowledge-index.py` nunca llega a ejecutarse —
    un mutante que sacara esa segunda carga del `try/except` (volviendo al defecto que el gap 45
    corrigió) seguía en verde con ese test solo. Aquí SOLO falta `knowledge-index.py`:
    `knowledge-schema.py` carga bien, así que la carga de `ki` SÍ se ejecuta de verdad — si el
    mutante la sacara del `try`, revienta con un traceback real en vez de degradar limpio."""
    import shutil
    with tempfile.TemporaryDirectory() as shared_falso:
        shutil.copy(os.path.join(cg.SHARED, "knowledge-schema.py"), shared_falso)
        # deliberadamente NO se copia knowledge-index.py
        monkeypatch.setattr(cg, "SHARED", shared_falso)
        with tempfile.TemporaryDirectory() as tmp:
            ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)
            veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
            assert exit_code == 2
            assert veredicto["errores"][0]["campo"] == "$"
            assert "no se encontro" in veredicto["errores"][0]["mensaje"]


# ------------------------------------------------------------------ gap 47: escalera de evidencia por defecto


def test_evidencia_sin_escalera_propia_usa_el_default_del_plugin():
    """Gap 47: un proyecto que declara sus PROPIAS categorias pero no su propia
    `evidence_levels` sigue usando la escalera por defecto del plugin para decidir si `evidencia`
    alcanza `min_evidence`, en vez de tratarlo como "no declarado en ningun sitio"."""
    with tempfile.TemporaryDirectory() as tmp:
        _taxonomy(tmp, [{"key": "GOTCHA", "folder": "gotchas", "min_evidence": "validated_case"}])
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)  # evidencia: validated_case
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 0
        assert veredicto["errores"] == []


def test_evidencia_fuera_de_toda_escalera_culpa_a_la_taxonomia():
    """Gap 47: si `evidencia` no esta NI en una escalera propia NI en la del plugin, el error
    apunta a `taxonomy.json` (campo `evidence_levels`), no al candidato — es la taxonomia la que
    se queda corta, no el candidato quien miente."""
    contenido = CANDIDATO_COMPLETO.replace("evidencia: validated_case", "evidencia: nivel-inventado")
    with tempfile.TemporaryDirectory() as tmp:
        _taxonomy(tmp, [{"key": "GOTCHA", "folder": "gotchas", "min_evidence": "validated_case"}])
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "evidence_levels" for e in veredicto["errores"])


# ------------------------------------------------------------------ gap 48: contencion del candidato


def test_candidato_en_approved_no_es_un_candidato():
    """Gap 48: un fichero que ya vive bajo `approved/` (o cualquier ruta fuera del arbol de
    candidatos) no es un candidato valido, aunque exista y tenga frontmatter correcto."""
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "docs", "knowledge", "approved", "gotchas")
        os.makedirs(d, exist_ok=True)
        ruta = os.path.join(d, "c.md")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(CANDIDATO_COMPLETO)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 2
        assert veredicto["errores"][0]["campo"] == "$"
        assert "no es un candidato" in veredicto["errores"][0]["mensaje"]


def test_candidato_fuera_del_arbol_del_proyecto_no_es_un_candidato():
    with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as otro:
        ruta = os.path.join(otro, "c.md")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(CANDIDATO_COMPLETO)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 2


# ------------------------------------------------------------------ gap 67: `rejected/` es terminal


def test_approve_sobre_candidato_en_rejected_es_error_de_uso():
    """Gap 67: `rejected/` es terminal (invariante fijado por el gap 49) — un candidato que ya vive
    ahi no admite `approve`, aunque el frontmatter sea perfectamente valido."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO, carpeta="rejected")
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 2
        assert veredicto["errores"][0]["campo"] == "$"
        assert "terminal" in veredicto["errores"][0]["mensaje"]


def test_needs_changes_sobre_candidato_en_rejected_es_error_de_uso():
    """Gap 67, simetrico para `needs_changes`."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO, carpeta="rejected")
        veredicto, exit_code = cg.evaluar(ruta, "needs_changes", root=tmp)
        assert exit_code == 2
        assert "terminal" in veredicto["errores"][0]["mensaje"]


def test_reject_sobre_candidato_ya_en_rejected_es_idempotente():
    """Gap 67: `--decision reject` sobre un candidato que YA vive en `rejected/` es idempotente
    (no es un error de uso volver a rechazar lo ya rechazado)."""
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO, carpeta="rejected")
        veredicto, exit_code = cg.evaluar(ruta, "reject", root=tmp)
        assert exit_code == 0
        assert veredicto["errores"] == []


# ------------------------------------------------------------------ gap 50: colision al aprobar


def test_approve_id_ya_existente_en_approved_bloquea():
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "docs", "knowledge", "approved", "gotchas")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "otro.md"), "w", encoding="utf-8") as f:
            f.write("---\nid: ca.gotcha.ejemplo\nversion: 1\nestado: aprobado\n---\n\n# ya aprobado\n")
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)  # mismo id: ca.gotcha.ejemplo
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "id" for e in veredicto["errores"])


def test_approve_nombre_de_fichero_ya_existente_en_destino_bloquea():
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "docs", "knowledge", "approved", "gotchas")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "c.md"), "w", encoding="utf-8") as f:
            f.write("---\nid: ca.gotcha.otro-id\nversion: 1\nestado: aprobado\n---\n\n# ya aprobado\n")
        ruta = _escribir(tmp, "c.md", CANDIDATO_COMPLETO)  # mismo nombre de fichero, id distinto
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "$" and "mismo nombre" in e["mensaje"] for e in veredicto["errores"])


# ------------------------------------------------------------------ gap 68: `--id` para candidatos sin `id` propio


def test_approve_sin_id_ni_override_avisa_colision_no_comprobada():
    """Gap 68: la guarda de colision de `id` (gap 50) es inerte si el candidato no declara `id` en
    su frontmatter — el caso mas expuesto: el candidato al que el Curator le va a asignar el `id` a
    mano (P4). Sin `--id` tampoco, debe avisar explicitamente de que no se comprobo."""
    contenido = CANDIDATO_COMPLETO.replace("id: ca.gotcha.ejemplo\n", "")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 0
        assert any(a["campo"] == "id" for a in veredicto["avisos"])


def test_approve_con_id_override_detecta_colision_aunque_el_candidato_no_lo_declare():
    """Gap 68: `--id` (`id_override`) deja comprobar la colision ANTES de que el Curator lo escriba
    en disco, incluso si el candidato todavia no trae `id` en su frontmatter."""
    contenido = CANDIDATO_COMPLETO.replace("id: ca.gotcha.ejemplo\n", "")
    with tempfile.TemporaryDirectory() as tmp:
        d = os.path.join(tmp, "docs", "knowledge", "approved", "gotchas")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "otro.md"), "w", encoding="utf-8") as f:
            f.write("---\nid: ca.gotcha.nuevo\nversion: 1\nestado: aprobado\n---\n\n# ya aprobado\n")
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp, id_override="ca.gotcha.nuevo")
        assert exit_code == 1
        assert any(e["campo"] == "id" for e in veredicto["errores"])
        assert veredicto["avisos"] == []


# ------------------------------------------------------------------ gap 53: reject/needs_changes sin category


def test_reject_sin_category_no_bloquea_y_avisa():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_SIN_CATEGORIA)
        veredicto, exit_code = cg.evaluar(ruta, "reject", root=tmp)
        assert exit_code == 0
        assert veredicto["errores"] == []
        assert any(a["campo"] == "category" for a in veredicto["avisos"])


def test_needs_changes_sin_category_no_bloquea_y_avisa():
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", CANDIDATO_SIN_CATEGORIA)
        veredicto, exit_code = cg.evaluar(ruta, "needs_changes", root=tmp)
        assert exit_code == 0
        assert any(a["campo"] == "category" for a in veredicto["avisos"])


# ------------------------------------------------------------------ gap 57: tags sin forma clave:valor


def test_approve_tag_sin_dos_puntos_bloquea():
    contenido = CANDIDATO_COMPLETO.replace("- area:testing", "- testing-sin-clave")
    with tempfile.TemporaryDirectory() as tmp:
        ruta = _escribir(tmp, "c.md", contenido)
        veredicto, exit_code = cg.evaluar(ruta, "approve", root=tmp)
        assert exit_code == 1
        assert any(e["campo"] == "tags" and "clave:valor" in e["mensaje"] for e in veredicto["errores"])
