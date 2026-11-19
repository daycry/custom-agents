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


if __name__ == "__main__":
    import unittest
    unittest.main()
