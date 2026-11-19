"""Tests de `backends/__init__.py::cargar_adaptador` (gap 95, fix1 2026-09-18, CWE-94/22):
`type` se valida contra `[a-z][a-z0-9-]*` ANTES de componer ninguna ruta de fichero."""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BACKENDS_DIR = os.path.normpath(os.path.join(HERE, "..", "backends"))
FIXTURES_DIR = os.path.join(HERE, "fixtures")  # adaptador de prueba (T-10): el plugin no incluye ninguno


def _cargar():
    spec = importlib.util.spec_from_file_location(
        "ks_backends_init_test", os.path.join(BACKENDS_DIR, "__init__.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ks_backends_init_test"] = mod
    spec.loader.exec_module(mod)
    return mod


binit = _cargar()


def test_adaptador_de_prueba_carga_por_directorios_extra():
    mod = binit.cargar_adaptador("adaptador-prueba", directorios=[FIXTURES_DIR])
    assert all(callable(getattr(mod, f)) for f in binit.FUNCIONES_OBLIGATORIAS)


def test_el_plugin_no_incluye_adaptadores_en_backends():
    """T-10: `backends/` solo trae el cargador y su README; el tipo de prueba no se resuelve ahi."""
    ficheros = sorted(n for n in os.listdir(BACKENDS_DIR) if n.endswith(".py"))
    assert ficheros == ["__init__.py"]
    try:
        binit.cargar_adaptador("adaptador-prueba", directorios=[BACKENDS_DIR])
        assert False
    except binit.AdaptadorNoDisponible as e:
        assert "no se encontró" in str(e)


def test_tipo_con_escape_de_ruta_es_rechazado_sin_tocar_disco():
    for tipo_malicioso in ("../x", "..\\x", "a/b", "a.b", "A", "-abc", ""):
        try:
            binit.cargar_adaptador(tipo_malicioso, directorios=[BACKENDS_DIR])
            assert False, f"debería haber levantado AdaptadorNoDisponible para {tipo_malicioso!r}"
        except binit.AdaptadorNoDisponible as e:
            assert "type" in str(e) or "inválido" in str(e)


def test_tipo_desconocido_pero_con_forma_valida_da_mensaje_de_no_encontrado():
    try:
        binit.cargar_adaptador("no-existe-de-verdad", directorios=[BACKENDS_DIR])
        assert False
    except binit.AdaptadorNoDisponible as e:
        assert "no se encontró" in str(e)


def test_adaptador_vacio_falla_con_mensaje_claro(tmp_path):
    """Un fichero de adaptador sin las 6 funciones falla el contrato con un mensaje que nombra las
    que faltan — nunca un traceback de `importlib` ni un `AttributeError` en tiempo de uso."""
    (tmp_path / "vacio.py").write_text("# adaptador aun no implementado\n", encoding="utf-8")
    try:
        binit.cargar_adaptador("vacio", directorios=[str(tmp_path)])
        assert False, "debería haber levantado AdaptadorNoDisponible"
    except binit.AdaptadorNoDisponible as e:
        mensaje = str(e)
        assert "no implementa el contrato completo" in mensaje
        for funcion in binit.FUNCIONES_OBLIGATORIAS:
            assert funcion in mensaje


def test_la_guia_add_backend_existe_y_la_citan_la_skill_setup_y_doctor_sin_prometer_sustitutos():
    """T-10: la skill, `/setup` y `/doctor` dejan de prometer backends concretos y remiten a la guía;
    ninguna de estas piezas nombra un sustituto concreto del backend retirado."""
    raiz = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
    guia = os.path.join(raiz, "skills", "knowledge-services", "references", "add-backend.md")
    assert os.path.isfile(guia)
    piezas = [os.path.join(raiz, *p) for p in (
        ("skills", "knowledge-services", "SKILL.md"), ("commands", "setup.md"), ("commands", "doctor.md"))]
    for ruta in piezas:
        with open(ruta, encoding="utf-8") as f:
            assert "add-backend.md" in f.read(), ruta
    for ruta in piezas + [guia, os.path.join(BACKENDS_DIR, "README.md"), os.path.join(BACKENDS_DIR, "__init__.py")]:
        with open(ruta, encoding="utf-8") as f:
            assert "kairos" not in f.read().lower(), ruta


if __name__ == "__main__":
    import unittest
    unittest.main()
