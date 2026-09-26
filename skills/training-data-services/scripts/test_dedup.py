"""Tests de `dedup.py` (training-data-services T-07, CA-10 y CA-06).

Near-duplicates entre versiones por shingles + Jaccard (la tecnica de `code-health.py`, sin
embeddings ni red), con el boilerplate fijo compartido fuera del calculo, sin comparacion O(n^2) de
todos los pares (filtro de prefijo sobre un indice invertido) y con resultado determinista.
"""
import importlib.util
import itertools
import json
import os
import random
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


def _load():
    spec = importlib.util.spec_from_file_location("tds_dedup", os.path.join(HERE, "dedup.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


dd = _load()

PALABRAS = ("rampa bola escalera puente torre arco cubo esfera cilindro cono muro suelo techo "
            "ventana puerta columna viga losa tejado balcon pasillo rueda eje muelle palanca "
            "polea engranaje cadena cuerda plano curva angulo radio altura anchura largo peso").split()

# Texto fijo largo (prompt de sistema), sin repeticiones: domina el Jaccard si no se filtra.
SISTEMA = "Eres un generador de geometria procedural. " + " ".join(
    random.Random(0).choice(PALABRAS) + "s" + str(i) for i in range(120))


def _frase(rng, n):
    return " ".join(rng.choice(PALABRAS) + str(rng.randrange(1000)) for _ in range(n))


def _grupos(r):
    return [list(g) for g in r["grupos"]]


# ------------------------------------------------------------------ criterio 1: near-duplicates

def test_t07_dos_versiones_casi_identicas_forman_un_grupo():
    base = "genera una rampa de treinta grados con anchura minima de medio metro y bola de radio diez"
    docs = [
        ("geo-ramp.steep@v001", "ramp", base),
        ("geo-ramp.steep@v002", "ramp", base + " y comprueba que no se sale"),
        ("geo-tower.tall@v001", "tower", "construye una torre de cinco pisos con balcon en el tercero"),
    ]
    r = dd.agrupar(docs, umbral=0.6)
    assert _grupos(r) == [["geo-ramp.steep@v001", "geo-ramp.steep@v002"]]


def test_t07_duplicado_exacto_y_texto_mas_corto_que_la_ventana():
    docs = [("a@v001", "f1", "hola"), ("a@v002", "f1", "hola"), ("b@v001", "f2", "adios")]
    assert _grupos(dd.agrupar(docs)) == [["a@v001", "a@v002"]]


def test_t07_componentes_conexas_transitivas():
    rng = random.Random(7)
    comun = _frase(rng, 40)
    a = comun + " " + _frase(rng, 6)
    b = a + " " + _frase(rng, 6)
    c = b + " " + _frase(rng, 6)
    j_ac = dd.jaccard(dd.shingles_de(a), dd.shingles_de(c))
    j_ab = dd.jaccard(dd.shingles_de(a), dd.shingles_de(b))
    umbral = (j_ac + j_ab) / 2
    assert j_ac < umbral <= j_ab
    r = dd.agrupar([("x@v001", "f", a), ("x@v002", "f", b), ("x@v003", "f", c)], umbral=umbral)
    assert _grupos(r) == [["x@v001", "x@v002", "x@v003"]]


def test_t07_el_umbral_es_configurable():
    rng = random.Random(3)
    comun = _frase(rng, 30)
    a, b = comun + " " + _frase(rng, 20), comun + " " + _frase(rng, 20)
    j = dd.jaccard(dd.shingles_de(a), dd.shingles_de(b))
    assert 0.2 < j < 0.8
    docs = [("a@v001", "f", a), ("a@v002", "f", b)]
    assert _grupos(dd.agrupar(docs, umbral=j - 0.01)) == [["a@v001", "a@v002"]]
    assert _grupos(dd.agrupar(docs, umbral=j + 0.01)) == []
    assert dd.UMBRAL_DEFECTO == 0.8


def test_t07_umbral_fuera_de_rango_es_error():
    for u in (0, -0.1, 1.5, float("nan")):
        with pytest.raises(ValueError):
            dd.agrupar([("a", "f", "x")], umbral=u)


# ------------------------------------------------------------------ criterio 2: boilerplate

def _con_boilerplate(n_familias=5, por_familia=3, seed=11):
    rng = random.Random(seed)
    docs = []
    for f in range(n_familias):
        for v in range(1, por_familia + 1):
            docs.append((f"geo-f{f}.x@v{v:03d}", f"f{f}", SISTEMA + " " + _frase(rng, 8)))
    return docs


def test_t07_texto_fijo_compartido_no_da_falsos_positivos():
    docs = _con_boilerplate()
    r = dd.agrupar(docs)
    assert _grupos(r) == []
    assert r["boilerplate"] > 0


def test_t07_sin_filtro_de_boilerplate_el_mismo_corpus_si_daria_falsos_positivos():
    """El filtro es lo que evita el falso positivo (mata el mutante que lo desactiva)."""
    docs = _con_boilerplate()
    r = dd.agrupar(docs, fraccion_boilerplate=1.0)
    assert r["boilerplate"] == 0
    assert _grupos(r), "sin filtro, el texto fijo domina y todo parece duplicado"


def test_t07_boilerplate_no_esconde_un_duplicado_real():
    docs = _con_boilerplate()
    rng = random.Random(99)
    extra = _frase(rng, 12)
    docs.append(("geo-dup.x@v001", "dup", SISTEMA + " " + extra))
    docs.append(("geo-dup.x@v002", "dup", SISTEMA + " " + extra + " fin"))
    assert _grupos(dd.agrupar(docs)) == [["geo-dup.x@v001", "geo-dup.x@v002"]]


def test_t07_un_grupo_grande_de_una_familia_no_se_confunde_con_boilerplate():
    """10 versiones casi iguales de UNA familia entre 12 casos: sus shingles estan en > 50 % de los
    casos pero en una sola familia -> no son boilerplate (el anti-leakage prefiere el falso positivo)."""
    rng = random.Random(5)
    base = _frase(rng, 30)
    docs = [(f"a@v{v:03d}", "fa", base + f" intento{v}") for v in range(1, 11)]
    docs += [("b@v001", "fb", _frase(rng, 30)), ("c@v001", "fc", _frase(rng, 30))]
    r = dd.agrupar(docs)
    assert _grupos(r) == [[f"a@v{v:03d}" for v in range(1, 11)]]


def test_t07_con_menos_de_tres_familias_no_hay_filtro_de_boilerplate():
    docs = _con_boilerplate(n_familias=2)
    r = dd.agrupar(docs)
    assert r["boilerplate"] == 0


def test_t07_caso_todo_boilerplate_solo_agrupa_con_su_identico():
    docs = _con_boilerplate()
    docs += [("geo-vacio.a@v001", "va", SISTEMA), ("geo-vacio.b@v001", "vb", SISTEMA)]
    r = dd.agrupar(docs)
    assert _grupos(r) == [["geo-vacio.a@v001", "geo-vacio.b@v001"]]


# ------------------------------------------------------------------ exactitud del filtro de prefijo

def _fuerza_bruta(docs, umbral, ventana, fraccion):
    """Referencia O(n^2): mismos shingles filtrados que `agrupar`, todos los pares."""
    conjuntos = dd._conjuntos(docs, ventana, fraccion)[0]
    padre = list(range(len(docs)))

    def find(x):
        while padre[x] != x:
            x = padre[x]
        return x
    for i, j in itertools.combinations(range(len(docs)), 2):
        si, sj = conjuntos[i], conjuntos[j]
        if si and sj and dd._supera(len(si & sj), len(si | sj), dd._fraccion(umbral)):
            padre[find(i)] = find(j)
    comp = {}
    for i in range(len(docs)):
        comp.setdefault(find(i), []).append(docs[i][0])
    return sorted(sorted(g) for g in comp.values() if len(g) > 1)


@pytest.mark.parametrize("umbral", [0.3, 0.5, 0.7, 0.8, 0.9, 1.0])
def test_t07_el_filtro_de_prefijo_da_lo_mismo_que_todos_los_pares(umbral):
    rng = random.Random(int(umbral * 100))
    docs = []
    for i in range(60):
        base = _frase(rng, rng.randrange(3, 25))
        docs.append((f"c{i:02d}@v001", f"f{i % 7}", base))
        if rng.random() < 0.5:
            mut = base.split()
            for _ in range(rng.randrange(0, 4)):
                mut[rng.randrange(len(mut))] = rng.choice(PALABRAS)
            docs.append((f"c{i:02d}@v002", f"f{i % 7}", " ".join(mut)))
    r = dd.agrupar(docs, umbral=umbral, ventana=2, fraccion_boilerplate=1.0)
    esperado = [g for g in _fuerza_bruta(docs, umbral, 2, 1.0)]
    # los componentes del filtro no tienen singletons; la referencia tampoco
    assert _grupos(r) == esperado


def test_t07_umbral_decimal_sin_error_de_coma_flotante():
    """0.7 * 10 = 7.000000000000001 en coma flotante: con `ceil` flotante el prefijo seria corto y se
    perderia el par con Jaccard EXACTO 0.7 (la comparacion es con enteros y fracciones)."""
    a = set(range(10))
    b = set(range(7)) | {100, 101, 102}
    assert dd._supera(len(a & b), len(a | b), dd._fraccion(0.7)) is False   # 7/13
    x = {str(i) for i in range(10)}
    y = {str(i) for i in range(7)}
    assert dd._supera(len(x & y), len(x | y), dd._fraccion(0.7)) is True    # 7/10 exacto


def test_t07_par_con_jaccard_exacto_en_el_umbral_se_agrupa():
    """|A| = 25, B ⊂ A con |B| = 14: Jaccard 14/25 = 0.56 EXACTO. En coma flotante 0.56 * 25 =
    14.000000000000002 y `ceil` daria 15: el prefijo de A tendria 11 shingles —los 11 que B no tiene,
    los mas raros— y el par no se veria nunca. Con la fraccion exacta el prefijo tiene 12."""
    a = " ".join(f"p{i:02d}" for i in range(25))
    b = " ".join(f"p{i:02d}" for i in range(14))
    docs = [("a@v001", "f", a), ("b@v001", "g", b)]
    assert _grupos(dd.agrupar(docs, umbral=0.56, ventana=1, fraccion_boilerplate=1.0)) == [["a@v001", "b@v001"]]


# ------------------------------------------------------------------ escala y determinismo

def test_t07_escala_no_compara_todos_los_pares():
    rng = random.Random(1)
    docs = [(f"c{i:05d}@v001", f"f{i % 50}", _frase(rng, 20)) for i in range(3000)]
    r = dd.agrupar(docs)
    assert _grupos(r) == []
    assert r["pares_verificados"] < 3000, r["pares_verificados"]   # O(n^2) serian ~4.5 millones


def test_t07_grupo_grande_no_verifica_cada_par():
    """1 000 copias identicas: las componentes se unen sin verificar los ~500 000 pares."""
    docs = [(f"c@v{i:04d}", "f", "la misma peticion exacta repetida muchas veces") for i in range(1, 1001)]
    r = dd.agrupar(docs)
    assert len(_grupos(r)) == 1 and len(_grupos(r)[0]) == 1000
    assert r["pares_verificados"] < 5000, r["pares_verificados"]


def test_t07_determinista_ante_el_orden_de_entrada():
    docs = _con_boilerplate() + [("z@v001", "z", "uno dos tres cuatro"), ("z@v002", "z", "uno dos tres cuatro")]
    rng = random.Random(4)
    for i in range(40):
        base = _frase(rng, 12)
        docs += [(f"k{i:02d}@v001", f"k{i % 4}", base), (f"k{i:02d}@v002", f"k{i % 4}", base + " " + _frase(rng, 3))]
    salidas = set()
    for semilla in range(6):
        barajado = list(docs)
        random.Random(semilla).shuffle(barajado)
        salidas.add(json.dumps(dd.agrupar(barajado, umbral=0.5), sort_keys=True))
    assert len(salidas) == 1   # tambien `pares_verificados`: el recorrido va en orden de id


def test_t07_pares_verificados_no_dependen_del_orden_de_entrada():
    """Corpus pequeño y denso (palabras de un vocabulario de 15): sin recorrer en orden de id, el
    atajo de «misma componente» ahorra verificaciones distintas segun el orden de entrada."""
    rng = random.Random(0)
    docs = [(f"d{i}", "f", " ".join(f"w{rng.randrange(15)}" for _ in range(6))) for i in range(12)]
    salidas = set()
    for semilla in range(5):
        barajado = list(docs)
        random.Random(semilla).shuffle(barajado)
        salidas.add(json.dumps(dd.agrupar(barajado, umbral=0.4, ventana=1, fraccion_boilerplate=1.0), sort_keys=True))
    assert len(salidas) == 1


def test_t07_ids_duplicados_son_error():
    with pytest.raises(ValueError):
        dd.agrupar([("a", "f", "x y z"), ("a", "f", "x y z")])


# ------------------------------------------------------------------ contenido variable del caso

def test_t07_texto_de_caso_incluye_peticion_contexto_y_trayectoria_no_restricciones_ni_metricas():
    caso = {
        "request": "PETICION literal",
        "context": {"text": "CONTEXTO", "refs": [{"ref": "src/a.py:1"}]},
        "constraints": {"nota": "RESTRICCION"},
        "metrics": {"m": "METRICA"},
        "trajectory": [
            {"role": "system", "content": "SISTEMA", "ts": "2026-01-01T00:00:00Z"},
            {"role": "assistant", "content": "", "tool_calls": [{"name": "HERRAMIENTA", "arguments": {"ARG": 1}}]},
            {"role": "tool", "name": "HERRAMIENTA", "content": "RESULTADO"},
        ],
    }
    t = dd.texto_de_caso(caso)
    for aguja in ("PETICION", "CONTEXTO", "SISTEMA", "HERRAMIENTA", "ARG", "RESULTADO"):
        assert aguja in t
    for fuera in ("RESTRICCION", "METRICA", "2026-01-01"):
        assert fuera not in t


def test_t07_texto_de_caso_objeto_con_claves_en_cualquier_orden_da_lo_mismo():
    a = {"request": {"b": 1, "a": 2}, "trajectory": [{"role": "user", "content": "x"}]}
    b = {"request": {"a": 2, "b": 1}, "trajectory": [{"role": "user", "content": "x"}]}
    assert dd.texto_de_caso(a) == dd.texto_de_caso(b)


# ------------------------------------------------------------------ CLI

def _cli(*args, entrada=None, env=None):
    return subprocess.run([sys.executable, os.path.join(HERE, "dedup.py"), *args], input=entrada,
                          capture_output=True, text=True, encoding="utf-8", env=env)


def test_t07_cli_agrupa_y_es_determinista_entre_procesos(tmp_path):
    f = tmp_path / "docs.jsonl"
    docs = _con_boilerplate() + [("z@v001", "z", "uno dos tres cuatro cinco"), ("z@v002", "z", "uno dos tres cuatro cinco")]
    f.write_text("".join(json.dumps({"id": i, "family": fam, "text": t}) + "\n" for i, fam, t in docs),
                 encoding="utf-8")
    salidas = set()
    for semilla in ("0", "1", "12345"):
        env = dict(os.environ, PYTHONHASHSEED=semilla)
        p = _cli(str(f), "--json", env=env)
        assert p.returncode == 0, p.stderr
        salidas.add(p.stdout)
    assert len(salidas) == 1
    assert json.loads(salidas.pop())["grupos"] == [["z@v001", "z@v002"]]


def test_t07_cli_errores_de_uso_sin_traceback(tmp_path):
    malo = tmp_path / "malo.jsonl"
    malo.write_text('{"id": "a", "family": "f"}\nno es json\n', encoding="utf-8")
    p = _cli(str(malo))
    assert p.returncode == 2 and "Traceback" not in p.stderr
    p = _cli(str(tmp_path / "no-existe.jsonl"))
    assert p.returncode == 2 and "Traceback" not in p.stderr
    bueno = tmp_path / "b.jsonl"
    bueno.write_text('{"id": "a", "family": "f", "text": "x"}\n', encoding="utf-8")
    p = _cli(str(bueno), "--umbral", "2")
    assert p.returncode == 2 and "Traceback" not in p.stderr


def test_t07_sin_red_ni_embeddings():
    fuente = open(os.path.join(HERE, "dedup.py"), encoding="utf-8").read()
    for prohibido in ("import socket", "urllib", "http.client", "requests", "numpy", "sklearn", "embedding("):
        assert prohibido not in fuente
