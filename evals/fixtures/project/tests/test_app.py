import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from app import exportar_csv, saludo  # noqa: E402


def test_saludo():
    assert saludo("Ana") == "Hola, Ana"


def test_exportar_csv():
    assert exportar_csv([[1, "a"], [2, "b"]]) == "1,a\n2,b"
