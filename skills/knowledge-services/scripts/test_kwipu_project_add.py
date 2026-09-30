"""Tests de `kwipu-project-add.py` (setup-statusline-polish T-12, C-07, diseno O1).

Todo ocurre en `tmp_path` con YAML sinteticos: nunca se toca un `projects.yaml` real. Los IDs
CA-09..CA-13 van en el nombre de los tests (la `Verificacion` del ledger los selecciona).
"""
import ast
import datetime
import errno
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "kwipu-project-add.py")


def _load():
    spec = importlib.util.spec_from_file_location("kpa_bajo_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kpa_bajo_test"] = mod
    spec.loader.exec_module(mod)
    return mod


kpa = _load()

# Muestra anonimizada de design.md: estilo de bloque, `projects:` ultima clave, 2 espacios,
# `root` relativa entre comillas dobles.
MUESTRA = (
    "# stack de ejemplo\n"
    "version: 1\n"
    "view:\n"
    "  output: kwipu/runtime/knowledge-view-v2\n"
    "projects:\n"
    "  otro-proyecto:\n"
    "    enabled: true\n"
    '    root: "../../../otro-proyecto/docs"\n'
    "    sources:\n"
    '      - path: "."\n'
    "        required: false\n"
    "  # comentario entre proyectos\n"
    "  tercero:\n"
    "    enabled: false\n"
    "    root: ../../../tercero/docs   # sin comillas\n"
)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def montar(tmp_path, yaml=MUESTRA, nombre="demo", export_dir=".claude/knowledge-services/kwipu-export",
           backend_type="markdown-export"):
    """Proyecto `proj/` (taxonomy.json) + stack `stack/kwipu/config/projects.yaml`."""
    proj = tmp_path / "proj"
    ks = proj / ".claude" / "knowledge-services"
    ks.mkdir(parents=True)
    tax = {
        "version": 1, "id_prefix": nombre,
        "categories": [{"key": "GOTCHA", "folder": "gotchas", "min_evidence": "observation"}],
        "backends": {"kwipu": {"type": backend_type, "enabled": True,
                               "config": {"export_dir": export_dir}}},
    }
    (ks / "taxonomy.json").write_text(json.dumps(tax), encoding="utf-8")
    cfg = tmp_path / "stack" / "kwipu" / "config"
    cfg.mkdir(parents=True)
    fich = cfg / "projects.yaml"
    if yaml is not None:
        fich.write_bytes(yaml if isinstance(yaml, bytes) else yaml.encode("utf-8"))
    return proj, tmp_path / "stack", fich


def correr(proj, stack, *extra, capsys=None):
    codigo = kpa.main(["--stack", str(stack), "--root", str(proj), *extra])
    cap = capsys.readouterr() if capsys is not None else None
    return codigo, cap


def apply_(proj, stack, fich, capsys, *extra):
    esperado = sha(fich.read_bytes())
    return correr(proj, stack, "--apply", "--esperado", esperado, *extra, capsys=capsys)


def copias(fich):
    return sorted(p for p in fich.parent.iterdir() if ".bak-" in p.name)


# ----------------------------------------------------------------------------------------------
# CA-09: alta feliz
# ----------------------------------------------------------------------------------------------
def test_ca09_vista_previa_no_escribe_y_da_sha(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    codigo, cap = correr(proj, stack, capsys=capsys)
    assert codigo == 0
    assert fich.read_bytes() == antes and copias(fich) == []
    assert "estado: nuevo" in cap.out and sha(antes) in cap.out
    assert "# >>> custom-agents:demo" in cap.out
    assert not (proj / ".claude" / "knowledge-services" / "kwipu-export").exists()


def test_ca09_apply_copia_bloque_y_root_relativa(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 0
    despues = fich.read_bytes()
    assert despues.startswith(antes) and len(despues) > len(antes)
    cs = copias(fich)
    assert len(cs) == 1 and cs[0].read_bytes() == antes
    assert re.fullmatch(r"projects\.yaml\.bak-\d{8}T\d{6}Z(-\d+)?", cs[0].name)
    bloque = despues[len(antes):].decode("utf-8")
    assert bloque.count("  demo:\n") == 1
    export = proj / ".claude" / "knowledge-services" / "kwipu-export"
    assert export.is_dir()                                   # se crea si no existe
    rel = os.path.relpath(export.resolve(), fich.parent.resolve()).replace(os.sep, "/")
    assert f'    root: "{rel}"' in bloque
    assert "# >>> custom-agents:demo" in bloque and "# <<< custom-agents:demo <<<" in bloque
    # imprime los comandos fijos, sin ejecutarlos
    assert "build_view" in cap.out and "docker compose restart kwipu kwipu-bridge kwipu-mcp" in cap.out
    # el resultado sigue siendo una forma reconocida y con el proyecto presente
    forma = kpa.analizar_yaml(despues)
    assert [p[0] for p in forma["proyectos"]] == ["otro-proyecto", "tercero", "demo"]


def test_ca09_segunda_pasada_es_noop(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    assert apply_(proj, stack, fich, capsys)[0] == 0
    tras = fich.read_bytes()
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 0 and "ya está dado de alta" in cap.out
    assert fich.read_bytes() == tras and len(copias(fich)) == 1


@pytest.mark.parametrize("yaml", [
    MUESTRA,
    MUESTRA.replace("\n", "\r\n"),
    MUESTRA.rstrip("\n"),                                   # sin fin de linea final
    "projects:\n",                                          # sin hijos
    "projects:   # nada aun\n",
    "top: 1\nprojects:\n    uno:\n        enabled: true\n        root: /abs/uno\n",   # 4 espacios
    "projects:\n  'con-comillas':\n    root: '../x'\n",
    "",                                                     # vacio -> no reconocido, ver otro test
])
def test_ca09_byte_a_byte_resto_identico(tmp_path, capsys, yaml):
    proj, stack, fich = montar(tmp_path, yaml=yaml)
    antes = fich.read_bytes()
    st_antes = os.stat(fich)
    if not antes.strip():
        assert correr(proj, stack, capsys=capsys)[0] == 3
        return
    codigo, _ = apply_(proj, stack, fich, capsys)
    assert codigo == 0
    despues = fich.read_bytes()
    assert despues[:len(antes)] == antes                    # ni un byte previo cambia
    anadido = despues[len(antes):]
    eol = b"\r\n" if b"\r\n" in antes else b"\n"
    if not antes.endswith(eol):
        assert anadido.startswith(eol)
    assert anadido.count(eol) == anadido.count(b"\n")       # eol uniforme en lo añadido
    st_despues = os.stat(fich)
    if st_antes.st_ino:
        assert st_antes.st_ino == st_despues.st_ino          # misma identidad
    assert copias(fich)[0].read_bytes() == antes


def test_ca09_sangria_de_cuatro_se_respeta(tmp_path, capsys):
    yaml = "projects:\n    uno:\n        enabled: true\n        root: /abs/uno\n"
    proj, stack, fich = montar(tmp_path, yaml=yaml)
    apply_(proj, stack, fich, capsys)
    bloque = fich.read_text(encoding="utf-8")[len(yaml):]
    assert "    demo:\n        enabled: true\n" in bloque
    assert "            required: false\n" in bloque


def test_ca09_json_de_la_vista_previa(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    codigo, cap = correr(proj, stack, "--json", capsys=capsys)
    datos = json.loads(cap.out)
    assert codigo == 0 and datos["estado"] == "nuevo" and datos["sha256"] == sha(fich.read_bytes())
    assert datos["nombre"] == "demo" and datos["escrito"] is False


# ----------------------------------------------------------------------------------------------
# CA-10: idempotencia
# ----------------------------------------------------------------------------------------------
def test_ca10_mismo_nombre_y_root_no_cambia_nada(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    export = proj / ".claude" / "knowledge-services" / "kwipu-export"
    rel = os.path.relpath(export, fich.parent.resolve()).replace(os.sep, "/")
    yaml = MUESTRA + f'  DEMO:\n    root: "{rel}"\n'          # mayusculas: mismo nombre
    fich.write_text(yaml, encoding="utf-8")
    antes = fich.read_bytes()
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 0 and "ya está dado de alta" in cap.out
    assert fich.read_bytes() == antes and copias(fich) == []


# ----------------------------------------------------------------------------------------------
# CA-11: forma no reconocida
# ----------------------------------------------------------------------------------------------
NO_RECONOCIDAS = {
    "bom": b"\xef\xbb\xbfprojects:\n",
    "no_utf8": b"projects:\n  a:\n    root: \xff\n",
    "eol_mezclado": b"a: 1\r\nprojects:\n  a:\n    root: x\n",
    "cr_aislado": b"a: 1\rprojects:\r",
    "tabuladores": b"projects:\n\ta:\n\t\troot: x\n",
    "documento": b"---\nprojects:\n  a:\n    root: x\n",
    "directiva": b"%YAML 1.2\nprojects:\n",
    "ancla": b"base: &b\n  x: 1\nprojects:\n  a:\n    root: x\n",
    "alias": b"projects:\n  a:\n    root: *b\n",
    "merge": b"projects:\n  a:\n    <<: {x: 1}\n",
    "inline_llaves": b"projects: {}\n",
    "inline_null": b"projects: null\n",
    "sin_projects": b"version: 1\n",
    "projects_duplicado": b"projects:\n  a:\n    root: x\nprojects:\n",
    "projects_no_ultimo": b"projects:\n  a:\n    root: x\nafter: 1\n",
    "hijo_inline": b"projects:\n  a: {root: x}\n",
    "hijo_lista": b"projects:\n  - a\n",
    "hijo_duplicado": b"projects:\n  a:\n    root: x\n  a:\n    root: y\n",
    "sangria_incoherente": b"projects:\n    a:\n      root: x\n  b:\n    root: y\n",
    "root_multilinea": b"projects:\n  a:\n    root: |\n      x\n",
    "root_plegado": b"projects:\n  a:\n    root: >\n      x\n",
    "root_vacio": b"projects:\n  a:\n    root:\n",
    "root_repetido": b"projects:\n  a:\n    root: x\n    root: y\n",
    "root_escape": b'projects:\n  a:\n    root: "x\\ny"\n',
    "root_sin_cerrar": b'projects:\n  a:\n    root: "x\n',
    "root_texto_tras_comillas": b'projects:\n  a:\n    root: "x" y\n',
    "root_comillas_simples_dobles": b"projects:\n  a:\n    root: 'it''s'\n",
    "marca_sin_cierre": b"projects:\n  # >>> custom-agents:zzz\n  zzz:\n    root: x\n",
    "campos_indentacion_incoherente": b"projects:\n  a:\n      root: x\n    enabled: true\n",
}


@pytest.mark.parametrize("clave", sorted(NO_RECONOCIDAS))
def test_ca11_forma_no_reconocida_no_escribe_e_imprime_bloque(tmp_path, capsys, clave):
    proj, stack, fich = montar(tmp_path, yaml=NO_RECONOCIDAS[clave])
    antes = fich.read_bytes()
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 3
    assert fich.read_bytes() == antes and copias(fich) == []
    assert "estado: no-reconocido" in cap.out
    assert "# >>> custom-agents:demo" in cap.out and "pega el bloque a mano" in cap.out
    assert not (proj / ".claude" / "knowledge-services" / "kwipu-export").exists()


def test_ca11_fichero_ausente_o_vacio(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path, yaml=None)
    codigo, cap = correr(proj, stack, capsys=capsys)
    assert codigo == 3 and not fich.exists() and "ausente" in cap.out
    fich.write_bytes(b"")
    assert correr(proj, stack, capsys=capsys)[0] == 3


def test_ca11_enlace_simbolico_y_duro(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    real = tmp_path / "real.yaml"
    real.write_bytes(fich.read_bytes())
    # enlace duro compartido
    dur = tmp_path / "duro.yaml"
    try:
        os.link(fich, dur)
    except OSError:
        pytest.skip("sin enlaces duros")
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 3 and "enlace duro" in cap.out and copias(fich) == []
    dur.unlink()
    # simbolico
    fich.unlink()
    try:
        os.symlink(real, fich)
    except (OSError, NotImplementedError):
        pytest.skip("sin enlaces simbolicos")
    antes = real.read_bytes()
    codigo, cap = correr(proj, stack, capsys=capsys)
    assert codigo == 3 and real.read_bytes() == antes


def test_ca11_directorio_config_como_enlace(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    cfg = fich.parent
    otro = tmp_path / "otro-config"
    cfg.rename(otro)
    try:
        os.symlink(otro, cfg, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("sin enlaces simbolicos")
    codigo, cap = correr(proj, stack, capsys=capsys)
    assert codigo == 3 and "es un enlace" in cap.out


def test_ca11_reconoce_variantes_validas():
    forma = kpa.analizar_yaml(
        b"# c\nprojects: # nota\n  # comentario\n  'a-b':\n    root: '../x y'   # c\n"
        b'    enabled: true\n  c:\n    root: "../z"\n  d:\n')
    assert forma["proyectos"] == [("a-b", "../x y"), ("c", "../z"), ("d", None)]
    assert forma["n"] == 2 and forma["paso"] == 2 and forma["eol"] == "\n"


# ----------------------------------------------------------------------------------------------
# CA-12: conflicto
# ----------------------------------------------------------------------------------------------
def test_ca12_homonimo_con_otra_root(tmp_path, capsys):
    yaml = MUESTRA + '  demo:\n    root: "../../../otra-cosa"\n'
    proj, stack, fich = montar(tmp_path, yaml=yaml)
    antes = fich.read_bytes()
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 4 and "otra `root`" in cap.out and "otro nombre" in cap.out
    assert fich.read_bytes() == antes and copias(fich) == []


def test_ca12_homonimo_sin_distinguir_mayusculas(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path, yaml=MUESTRA + "  Demo:\n    enabled: true\n")
    codigo, cap = correr(proj, stack, capsys=capsys)
    assert codigo == 4 and "sin `root` legible" in cap.out


def test_ca12_misma_root_otro_nombre(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    export = proj / ".claude" / "knowledge-services" / "kwipu-export"
    rel = os.path.relpath(export, fich.parent.resolve()).replace(os.sep, "/")
    fich.write_text(MUESTRA + f'  ajeno:\n    root: "{rel}"\n', encoding="utf-8")
    antes = fich.read_bytes()
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 4 and "ya está dada de alta como `ajeno`" in cap.out
    assert fich.read_bytes() == antes and copias(fich) == []


def test_ca12_nombre_alternativo_resuelve(tmp_path, capsys):
    yaml = MUESTRA + '  demo:\n    root: "../../../otra-cosa"\n'
    proj, stack, fich = montar(tmp_path, yaml=yaml)
    codigo, _ = apply_(proj, stack, fich, capsys, "--nombre", "demo-2")
    assert codigo == 0 and b"  demo-2:\n" in fich.read_bytes()


# ----------------------------------------------------------------------------------------------
# CA-13: sin confirmacion o con fallo de la copia, no escribe; nada de ejecutar el stack
# ----------------------------------------------------------------------------------------------
def test_ca13_sin_esperado_o_con_hash_distinto(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    assert correr(proj, stack, "--apply", capsys=capsys)[0] == 2        # #13 (fix1): uso, no E/S
    assert correr(proj, stack, "--apply", "--esperado", "0" * 64, capsys=capsys)[0] == 1
    assert fich.read_bytes() == antes and copias(fich) == []


def test_ca13_el_fichero_cambia_entre_vista_previa_y_apply(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    esperado = sha(fich.read_bytes())
    fich.write_bytes(fich.read_bytes() + b"  # editado a mano\n")
    editado = fich.read_bytes()
    codigo, cap = correr(proj, stack, "--apply", "--esperado", esperado, capsys=capsys)
    assert codigo == 1 and "cambió" in cap.out
    assert fich.read_bytes() == editado and copias(fich) == []


def test_ca13_fallo_de_la_copia_aborta_sin_escribir(tmp_path, capsys, monkeypatch):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()

    def rota(*a, **k):
        raise OSError("disco lleno")

    monkeypatch.setattr(kpa, "_crear_copia", rota)
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 1 and "copia de seguridad" in cap.out
    assert fich.read_bytes() == antes


def test_ca13_no_ejecuta_nada_del_stack():
    arbol = ast.parse(open(SCRIPT, encoding="utf-8").read())
    importados = set()
    llamadas = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            importados |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            importados.add((n.module or "").split(".")[0])
        elif isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "os":
            llamadas.add(n.attr)
    assert not importados & {"subprocess", "socket", "urllib", "http", "requests"}
    assert not llamadas & {"system", "popen", "exec", "execv", "execvp", "spawnl", "startfile"}


def test_ca13_grep_de_la_verificacion_sin_coincidencias():
    """Mismo criterio que el grep de la Verificacion del ledger: ni una linea."""
    for n, l in enumerate(open(SCRIPT, encoding="utf-8"), 1):
        assert not re.search(r"subprocess|os\.system", l), f"linea {n}: {l!r}"


# ----------------------------------------------------------------------------------------------
# Escritura: reversion y copias
# ----------------------------------------------------------------------------------------------
def test_fix1_1_otro_escritor_que_anade_despues_no_se_borra(tmp_path, capsys, monkeypatch):
    """#1 (fix1): lo que sobra NO es solo el bloque propio -otro escritor añadió detras-, asi que
    no se trunca nada (antes se truncaba a `len(previo)` y se borraban los bytes ajenos)."""
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    real = os.write

    def sucia(fd, datos):
        n = real(fd, datos)
        real(fd, b"# basura concurrente\n")
        return n

    monkeypatch.setattr(kpa, "_os_write", sucia)
    codigo, cap = apply_(proj, stack, fich, capsys)
    final = fich.read_bytes()
    assert final.endswith(b"# basura concurrente\n"), "un byte ajeno borrado"
    assert final.startswith(antes) and b"# >>> custom-agents:demo" in final
    assert codigo == 1 and "cambió durante la escritura" in cap.out and "SÍ está" in cap.out
    assert "copia en" in cap.out and copias(fich)[0].read_bytes() == antes


def test_prefijo_alterado_no_se_toca_y_se_senala_la_copia(tmp_path, capsys, monkeypatch):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    real = os.write

    def mutante(fd, datos):
        n = real(fd, datos)
        with open(fich, "r+b") as f:                       # otro escritor altera el inicio
            f.write(b"X")
        return n

    monkeypatch.setattr(kpa, "_os_write", mutante)
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 1 and "prefijo alterado" in cap.out and "copia en" in cap.out
    assert fich.read_bytes()[0:1] == b"X" and fich.read_bytes() != antes
    assert b"# >>> custom-agents:demo" in fich.read_bytes() and "SÍ está" in cap.out
    assert copias(fich)[0].read_bytes() == antes


def test_escritura_corta_se_revierte(tmp_path, capsys, monkeypatch):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    real = os.write
    monkeypatch.setattr(kpa, "_os_write", lambda fd, d: real(fd, d[: len(d) // 2]))
    codigo, _ = apply_(proj, stack, fich, capsys)
    assert codigo == 1 and fich.read_bytes() == antes


def test_error_de_io_al_escribir(tmp_path, capsys, monkeypatch):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()

    def falla(fd, d):
        raise OSError("boom")

    monkeypatch.setattr(kpa, "_os_write", falla)
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 1 and "error de E/S" in cap.out and fich.read_bytes() == antes


def test_el_fichero_cambia_justo_antes_de_escribir(tmp_path):
    proj, stack, fich = montar(tmp_path)
    previo, st = kpa._leer_fichero(str(fich))
    fich.write_bytes(previo + b"# otro\n")
    ok, msg, presente = kpa.escribir_anadiendo(str(fich), previo, st, b"x\n")
    assert ok is False and "cambió" in msg and fich.read_bytes() == previo + b"# otro\n"
    assert presente is False


def test_copias_nunca_pisan_otra(tmp_path, monkeypatch):
    proj, stack, fich = montar(tmp_path)
    real_dt = datetime.datetime

    class Fijo(real_dt):
        @classmethod
        def now(cls, tz=None):
            return real_dt(2026, 1, 2, 3, 4, 5, tzinfo=tz)

    monkeypatch.setattr(kpa, "datetime", types.SimpleNamespace(
        datetime=Fijo, timezone=datetime.timezone, date=datetime.date))
    a = kpa._crear_copia(str(fich), b"uno")
    b = kpa._crear_copia(str(fich), b"dos")
    assert os.path.basename(a) == "projects.yaml.bak-20260102T030405Z"
    assert os.path.basename(b) == "projects.yaml.bak-20260102T030405Z-1"
    assert open(a, "rb").read() == b"uno" and open(b, "rb").read() == b"dos"


def test_copia_que_no_coincide_se_descarta(tmp_path, monkeypatch):
    proj, stack, fich = montar(tmp_path)
    real = os.write
    monkeypatch.setattr(kpa.os, "write", lambda fd, d: real(fd, d[:-1] if d else d))
    with pytest.raises(OSError):
        kpa._crear_copia(str(fich), b"abcdef")
    assert copias(fich) == []


# ----------------------------------------------------------------------------------------------
# Entradas inyectadas y errores de uso
# ----------------------------------------------------------------------------------------------
@pytest.mark.parametrize("nombre", [
    "a\nb: c", "a:b", "a#b", 'a"b', "a'b", "..", "../x", "a/b", "a\\b", "-x", "Demo", "a b",
    "", "x" * 65, "a\rb", "a\x00b", "é",
])
def test_inyeccion_en_el_nombre_se_rechaza(tmp_path, capsys, nombre):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    codigo, cap = correr(proj, stack, "--nombre=" + nombre, "--apply", "--esperado", "x", capsys=capsys)
    assert codigo == 2 and fich.read_bytes() == antes and copias(fich) == []


@pytest.mark.parametrize("root", ['a"b', "a\\b", "a\nb", "a\rb", "a\x00b", ""])
def test_inyeccion_en_la_root_se_rechaza(root):
    with pytest.raises(kpa.Uso):
        kpa.validar_root(root)


def test_root_con_dos_puntos_almohadilla_y_espacios_va_entre_comillas():
    forma = {"eol": "\n", "n": 2, "paso": 2}
    bloque = kpa.construir_bloque("demo", "../a b/c:d#e", forma, "2026-01-01")
    assert '    root: "../a b/c:d#e"\n' in bloque
    assert kpa.analizar_yaml(("projects:\n" + bloque).encode())["proyectos"] == [("demo", "../a b/c:d#e")]


def test_id_prefix_invalido_en_taxonomia(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path, nombre="Mal Nombre")
    assert correr(proj, stack, capsys=capsys)[0] == 2


def test_export_dir_fuera_del_proyecto_o_traversal(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path, export_dir="../fuera")
    codigo, cap = correr(proj, stack, capsys=capsys)
    assert codigo == 2 and "fuera de la raíz" in cap.err
    proj, stack, fich = montar(tmp_path / "b", export_dir="..")
    assert correr(proj, stack, capsys=capsys)[0] == 2
    proj, stack, fich = montar(tmp_path / "c", export_dir="docs/knowledge/approved/x")
    assert correr(proj, stack, capsys=capsys)[0] == 2


def test_taxonomia_sin_backend_markdown_export(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path, backend_type="graphiti")
    assert correr(proj, stack, capsys=capsys)[0] == 2
    proj, stack, fich = montar(tmp_path / "b")
    assert correr(proj, stack, "--backend", "no-existe", capsys=capsys)[0] == 2


def test_stack_invalido(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    assert kpa.main(["--stack", str(tmp_path / "nada"), "--root", str(proj)]) == 2
    (tmp_path / "vacio").mkdir()
    assert kpa.main(["--stack", str(tmp_path / "vacio"), "--root", str(proj)]) == 2
    assert kpa.main(["--stack", "x\ny", "--root", str(proj)]) == 2
    capsys.readouterr()


def test_taxonomia_invalida(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    (proj / ".claude" / "knowledge-services" / "taxonomy.json").write_text("{no json", encoding="utf-8")
    assert correr(proj, stack, capsys=capsys)[0] == 2


def test_modulo_compartido_ausente(tmp_path, monkeypatch, capsys):
    proj, stack, fich = montar(tmp_path)
    monkeypatch.setattr(kpa, "SHARED", str(tmp_path / "no-existe"))
    assert correr(proj, stack, capsys=capsys)[0] == 2


def test_modulo_compartido_roto(tmp_path, monkeypatch, capsys):
    proj, stack, fich = montar(tmp_path)
    (tmp_path / "sh").mkdir()
    (tmp_path / "sh" / "knowledge-schema.py").write_text("raise RuntimeError('x')", encoding="utf-8")
    monkeypatch.setattr(kpa, "SHARED", str(tmp_path / "sh"))
    assert correr(proj, stack, capsys=capsys)[0] == 2


def test_root_absoluta_si_no_hay_relativa(monkeypatch):
    def sin_relativa(*a, **k):
        raise ValueError("otra unidad")

    monkeypatch.setattr(kpa.os.path, "relpath", sin_relativa)
    assert kpa.calcular_root("/abs/export", "/abs/cfg") == "/abs/export"


def test_comandos_fijos_con_stack_citado():
    cmds = kpa._comandos("/ruta con espacios/stack")
    assert cmds[0].startswith("cd ") and "espacios" in cmds[0] and "'" in cmds[0]
    assert cmds[1].endswith("--output kwipu/runtime/knowledge-view-v2")
    assert cmds[2] == "docker compose restart kwipu kwipu-bridge kwipu-mcp"


def test_cli_como_proceso(tmp_path):
    proj, stack, fich = montar(tmp_path)
    r = subprocess.run([sys.executable, SCRIPT, "--stack", str(stack), "--root", str(proj), "--json"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0 and json.loads(r.stdout)["estado"] == "nuevo"
    r = subprocess.run([sys.executable, SCRIPT, "--stack", str(tmp_path / "nada"), "--root", str(proj)],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 2


def test_lectura_sin_permiso_o_directorio_como_fichero(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path, yaml=None)
    fich.mkdir()
    codigo, cap = correr(proj, stack, capsys=capsys)
    assert codigo == 3 and "no es un fichero regular" in cap.out


# ----------------------------------------------------------------------------------------------
# fix1 de la revisión (intento 1): #1/#7 truncado seguro, #2 nombres, #9 escapado, #10 enlaces,
# #11 clave `root`, #13 uso, #5 espejo EN. Todo en `tmp_path`.
# ----------------------------------------------------------------------------------------------
BLOQUE_B = (b"  # >>> custom-agents:otro-setup\n  otro-setup:\n    root: \"../b\"\n"
            b"  # <<< custom-agents:otro-setup <<<\n")


def test_fix1_1_dos_setup_intercalados_no_borran_ningun_bloque(tmp_path, capsys, monkeypatch):
    """#1: el `/setup` B completa su alta dentro de la ventana de A (entre el `fstat` y el `write`
    de A). Antes, la verificacion de A truncaba a `len(previo)` y borraba el bloque de B, que B ya
    habia dado por añadido. Ahora quedan los dos y A informa del estado real."""
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    previo, st = kpa._leer_fichero(str(fich))
    real = os.write
    dentro = []

    def intercalada(fd, datos):
        if not dentro:
            dentro.append(fd)
            kpa.escribir_anadiendo(str(fich), previo, st, BLOQUE_B)     # B, entero, en medio
        return real(fd, datos)

    monkeypatch.setattr(kpa, "_os_write", intercalada)
    codigo, cap = apply_(proj, stack, fich, capsys)
    final = fich.read_bytes()
    assert BLOQUE_B in final, "el bloque de B (ya añadido) se borró"
    assert b"# >>> custom-agents:demo" in final and final.startswith(antes)
    assert codigo == 1 and "cambió durante la escritura" in cap.out and "SÍ está" in cap.out


def test_fix1_1_editor_que_guarda_por_rename_no_pierde_la_edicion(tmp_path, capsys, monkeypatch):
    """#1: un editor guarda por rename entre el `write` y la relectura. El truncado por RUTA
    cortaba el fichero nuevo del editor (se perdia la edicion). Ahora la ruta ya no es el
    descriptor: no se toca y se nombra el estado real del fichero que hay en la ruta."""
    proj, stack, fich = montar(tmp_path)
    real = os.write
    esperado = []

    def editor(fd, datos):
        n = real(fd, datos)
        contenido = fich.read_bytes() + b"  # edicion del usuario\n"
        tmp = fich.parent / "projects.yaml.editor"
        tmp.write_bytes(contenido)
        try:
            os.replace(tmp, fich)
        except PermissionError:
            tmp.unlink()
            pytest.skip("este sistema no reemplaza un fichero abierto (Windows): el caso no existe")
        esperado.append(contenido)
        return n

    monkeypatch.setattr(kpa, "_os_write", editor)
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert fich.read_bytes() == esperado[0], "se perdió la edición del usuario"
    assert codigo == 1 and "cambió durante la escritura" in cap.out and "SÍ está" in cap.out


def test_fix1_7_fsync_con_eio_tras_escribir_informa_el_estado_real(tmp_path, capsys, monkeypatch):
    """#7: el `fsync` del append lanza EIO. Antes la excepcion se saltaba la verificacion: el
    bloque quedaba escrito y se informaba `escrito: false`. Ahora se verifica y, como lo que sobra
    es exactamente lo propio con la identidad intacta, se revierte y se dice."""
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    real_write, real_fsync = os.write, os.fsync
    tras = []

    def escribe(fd, datos):
        n = real_write(fd, datos)
        tras.append(fd)
        return n

    def fsync(fd):
        if tras:
            raise OSError(errno.EIO, "EIO simulado")
        return real_fsync(fd)

    monkeypatch.setattr(kpa, "_os_write", escribe)
    monkeypatch.setattr(kpa.os, "fsync", fsync)
    codigo, cap = apply_(proj, stack, fich, capsys, "--json")
    datos = json.loads(cap.out)
    assert fich.read_bytes() == antes, "el bloque quedó escrito"
    assert codigo == 1 and datos["escrito"] is False and datos["bloque_presente"] is False
    assert "revirtió" in datos["mensaje"] and "NO está" in datos["mensaje"]


def test_fix1_7_estado_real_si_no_se_puede_revertir(tmp_path, capsys, monkeypatch):
    """#7: si tampoco se puede truncar, el bloque sigue ahi y asi se informa (`escrito: true`)."""
    proj, stack, fich = montar(tmp_path)
    real_write, real_fsync = os.write, os.fsync
    tras = []

    def escribe(fd, datos):
        tras.append(fd)
        return real_write(fd, datos)

    def fsync(fd):
        if tras:
            raise OSError(errno.EIO, "EIO simulado")
        return real_fsync(fd)

    def sin_truncar(fd, tam):
        raise OSError(errno.EIO, "ftruncate roto")

    monkeypatch.setattr(kpa, "_os_write", escribe)
    monkeypatch.setattr(kpa.os, "fsync", fsync)
    monkeypatch.setattr(kpa.os, "ftruncate", sin_truncar)
    codigo, cap = apply_(proj, stack, fich, capsys, "--json")
    datos = json.loads(cap.out)
    assert b"# >>> custom-agents:demo" in fich.read_bytes()
    assert codigo == 1 and datos["escrito"] is True and datos["bloque_presente"] is True
    assert "no se pudo revertir" in datos["mensaje"] and "SÍ está" in datos["mensaje"]


def test_fix1_10_enlace_duro_creado_antes_de_escribir_no_recibe_el_bloque(tmp_path):
    """#10: `nlink == 1` se comprueba tambien en el `fstat` previo al `write`."""
    proj, stack, fich = montar(tmp_path)
    previo, st = kpa._leer_fichero(str(fich))
    otro = tmp_path / "duro.yaml"
    try:
        os.link(fich, otro)
    except OSError:
        pytest.skip("sin enlaces duros")
    r = kpa.escribir_anadiendo(str(fich), previo, st, b"  # x\n")
    assert fich.read_bytes() == previo and otro.read_bytes() == previo
    assert r[0] is False and "cambió antes de escribir" in r[1]


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="sin O_NOFOLLOW (Windows)")
def test_fix1_10_la_escritura_no_sigue_un_enlace_simbolico(tmp_path, monkeypatch):
    """#10: aun si la identidad no se pudiera comprobar, la escritura se abre con `O_NOFOLLOW`."""
    proj, stack, fich = montar(tmp_path)
    previo, st = kpa._leer_fichero(str(fich))
    victima = tmp_path / "victima.yaml"
    victima.write_bytes(previo)
    fich.unlink()
    os.symlink(victima, fich)
    monkeypatch.setattr(kpa, "_misma_identidad", lambda a, b: True)
    try:
        r = kpa.escribir_anadiendo(str(fich), previo, st, b"  # x\n")
        assert r[0] is False
    except OSError:
        pass
    assert victima.read_bytes() == previo


@pytest.mark.parametrize("nombre", [
    "2024", "2048", "0x1f", "0b101", "1e3", "y", "n", "yes", "no", "on", "off", "true", "false", "null",
])
def test_fix1_2_nombre_que_yaml_no_lee_como_texto_se_rechaza(tmp_path, capsys, nombre):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    codigo, cap = apply_(proj, stack, fich, capsys, "--nombre", nombre)
    assert codigo == 2 and fich.read_bytes() == antes and copias(fich) == []
    assert f"prueba `--nombre p-{nombre}`" in cap.err
    assert kpa.nombre_valido(f"p-{nombre}")


def test_fix1_2_carpeta_2048_sin_id_prefix_no_produce_un_nombre_numerico(tmp_path, capsys):
    """El `id_prefix` por defecto sale del slug de la carpeta: `2048` daba una clave int en YAML."""
    proj, stack, fich = montar(tmp_path)
    tax = proj / ".claude" / "knowledge-services" / "taxonomy.json"
    datos = json.loads(tax.read_text(encoding="utf-8"))
    del datos["id_prefix"]
    tax.write_text(json.dumps(datos), encoding="utf-8")
    carpeta = tmp_path / "2048"
    proj.rename(carpeta)
    antes = fich.read_bytes()
    codigo, cap = correr(carpeta, stack, "--apply", "--esperado", sha(antes), capsys=capsys)
    assert codigo == 2 and fich.read_bytes() == antes
    assert "prueba `--nombre p-2048`" in cap.err


@pytest.mark.parametrize("root", ["a‮b", "a\u0085b", "a b", "a b", "a​b",
                                  "a﻿b", "a­b", "a\x9bb"])
def test_fix1_9_validar_root_rechaza_cc_cf_zl_zp(root):
    with pytest.raises(kpa.Uso):
        kpa.validar_root(root)


def test_fix1_9_validar_root_admite_zwj_y_zwnj():
    assert kpa.validar_root("a‍b‌c") == "a‍b‌c"


def test_fix1_9_texto_de_projects_yaml_se_escapa_en_la_terminal(tmp_path, capsys):
    """#9: claves entre comillas con ESC/C1 (duplicado) o BEL/bidi (conflicto) salian crudas."""
    hostil = '"a\x1b[31m\x9b"'
    proj, stack, fich = montar(tmp_path, yaml=f"projects:\n  {hostil}:\n    root: x\n  {hostil}:\n    root: y\n")
    codigo, cap = correr(proj, stack, capsys=capsys)
    assert codigo == 3 and "duplicado" in cap.out
    assert "\x1b" not in cap.out and "\x9b" not in cap.out and "\\x1b" in cap.out

    proj, stack, fich = montar(tmp_path / "b")
    export = proj / ".claude" / "knowledge-services" / "kwipu-export"
    rel = os.path.relpath(export, fich.parent.resolve()).replace(os.sep, "/")
    fich.write_text(MUESTRA + f'  "x\x07‮y":\n    root: "{rel}"\n', encoding="utf-8")
    codigo, cap = correr(proj, stack, capsys=capsys)
    assert codigo == 4 and "dada de alta como" in cap.out
    assert "\x07" not in cap.out and "‮" not in cap.out and "\\x07" in cap.out


def test_fix1_9_la_ruta_de_la_entrada_se_escapa_en_la_terminal(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    raro = tmp_path / "st‮ack"
    (tmp_path / "stack").rename(raro)
    codigo, cap = correr(proj, raro, capsys=capsys)
    assert codigo == 0 and "‮" not in cap.out and "\\u202e" in cap.out


@pytest.mark.parametrize("clave", ['"root"', "'root'", "root ", '"root"  ', "'root' "])
def test_fix1_11_clave_root_con_comillas_o_espacios_se_reconoce(tmp_path, capsys, clave):
    """#11: con `"root":` o `root :` la `root` quedaba `None` y no saltaba el conflicto."""
    proj, stack, fich = montar(tmp_path)
    export = proj / ".claude" / "knowledge-services" / "kwipu-export"
    rel = os.path.relpath(export, fich.parent.resolve()).replace(os.sep, "/")
    fich.write_text(MUESTRA + f'  ajeno:\n    {clave}: "{rel}"\n', encoding="utf-8")
    antes = fich.read_bytes()
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 4 and "ya está dada de alta como `ajeno`" in cap.out
    assert fich.read_bytes() == antes and copias(fich) == []


@pytest.mark.parametrize("linea", ["root\t: x", '"root"\t: x', '"ro\\x6ft": x', "? root", "root:x"])
def test_fix1_11_otra_forma_de_la_clave_root_es_forma_no_reconocida(tmp_path, capsys, linea):
    proj, stack, fich = montar(tmp_path, yaml=MUESTRA + f"  ajeno:\n    {linea}\n    enabled: true\n")
    antes = fich.read_bytes()
    codigo, cap = apply_(proj, stack, fich, capsys)
    assert codigo == 3 and "no-reconocido" in cap.out
    assert fich.read_bytes() == antes and copias(fich) == []


def test_fix1_13_apply_sin_esperado_es_error_de_uso(tmp_path, capsys):
    proj, stack, fich = montar(tmp_path)
    antes = fich.read_bytes()
    codigo, cap = correr(proj, stack, "--apply", capsys=capsys)
    assert codigo == 2 and "--esperado" in cap.out and fich.read_bytes() == antes


def test_fix1_5_la_fila_en_del_readme_nombra_el_alta_en_kwipu():
    """#5: la fila `knowledge-services` de `docs/en/README.md` espeja a la de `docs/README.md`."""
    raiz = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
    for rel in (("docs", "README.md"), ("docs", "en", "README.md")):
        with open(os.path.join(raiz, *rel), encoding="utf-8") as f:
            fila = next(l for l in f if l.startswith("| **knowledge-services** |"))
        assert "kwipu-project-add.py" in fila, "/".join(rel)
