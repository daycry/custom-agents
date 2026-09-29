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

def _con_boilerplate(n_familias=7, por_familia=3, seed=11):
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
    casos, pero con menos de `N_MIN_BOILERPLATE` casos no se filtra nada (H1): siguen agrupadas."""
    rng = random.Random(5)
    base = _frase(rng, 30)
    docs = [(f"a@v{v:03d}", "fa", base + f" intento{v}") for v in range(1, 11)]
    docs += [("b@v001", "fb", _frase(rng, 30)), ("c@v001", "fc", _frase(rng, 30))]
    r = dd.agrupar(docs)
    assert _grupos(r) == [[f"a@v{v:03d}" for v in range(1, 11)]]


def test_t07_con_menos_de_n_min_casos_no_hay_filtro_de_boilerplate():
    """H1: con menos de `N_MIN_BOILERPLATE` (20) casos no se filtra nada, ni con muchas familias."""
    assert dd.N_MIN_BOILERPLATE == 20 and dd.BOILERPLATE_DEFECTO == 0.5
    docs = _con_boilerplate(n_familias=19, por_familia=1)
    assert len(docs) == 19
    assert dd.agrupar(docs)["boilerplate"] == 0
    assert dd.agrupar(_con_boilerplate(n_familias=20, por_familia=1))["boilerplate"] > 0


def test_t07_dos_familias_con_el_mismo_prompt_de_sistema_si_se_filtra():
    """#115a: sin la regla de familias, el prompt de sistema compartido por DOS familias es plantilla."""
    docs = _con_boilerplate(n_familias=2, por_familia=12)
    r = dd.agrupar(docs)
    assert r["boilerplate"] > 0 and _grupos(r) == []
    assert "min_familias_boilerplate" not in r["parametros"]
    assert r["parametros"]["n_min_boilerplate"] == 20


def test_t07_bloque_en_la_mitad_justa_no_es_boilerplate():
    """`df > fraccion · n` estricto: un bloque en EXACTAMENTE la mitad de 20 casos no se filtra."""
    rng = random.Random(8)
    comun = _frase(rng, 30)
    docs = [(f"m{i:02d}@v001", f"f{i}", (comun + " " if i < 10 else "") + _frase(rng, 30)) for i in range(20)]
    assert dd.agrupar(docs)["boilerplate"] == 0
    docs[10] = ("m10@v001", "f10", comun + " " + _frase(rng, 30))
    assert dd.agrupar(docs)["boilerplate"] > 0


def test_t07_fraccion_menor_que_uno_entre_n_todo_es_plantilla():
    """`fraccion < 1/n`: hasta un shingle de un solo caso supera `fraccion · n` -> todo es plantilla y
    solo se agrupan los duplicados exactos (por su conjunto original)."""
    docs = _con_boilerplate(n_familias=10, por_familia=2)
    docs.append(("dup@v001", "d", docs[0][2]))
    r = dd.agrupar(docs, fraccion_boilerplate=0.01)
    distintos = len({s for _i, _f, t in docs for s in dd.shingles_de(t)})
    assert r["boilerplate"] == distintos
    assert _grupos(r) == [sorted([docs[0][0], "dup@v001"])]


# ------------------------------------------------------------------ #114: la fuga entre familias

def _peticion_21(rng):
    return " ".join(f"{rng.choice(PALABRAS)}{rng.randrange(1000)}" for _ in range(21))


def test_t07_114_near_duplicate_entre_cuatro_familias_se_agrupa():
    """#114: peticion de 21 palabras + UNA distinta en 4 familias (Jaccard 0.9): antes, 18 shingles se
    tomaban por boilerplate y el grupo desaparecia (fuga del benchmark a train)."""
    rng = random.Random(114)
    base = _peticion_21(rng)
    docs = [(f"geo-{fam}.x@v001", fam, base + " " + extra)
            for fam, extra in (("bench", "alfa"), ("fa", "beta"), ("fb", "gamma"), ("fc", "delta"))]
    r = dd.agrupar(docs)
    assert r["boilerplate"] == 0
    assert _grupos(r) == [sorted(d[0] for d in docs)]
    # tambien con 3 de 5 casos
    docs5 = docs[:3] + [("geo-fd.x@v001", "fd", _peticion_21(rng)), ("geo-fe.x@v001", "fe", _peticion_21(rng))]
    assert _grupos(dd.agrupar(docs5)) == [sorted(d[0] for d in docs[:3])]


def _plantilla(palabras, seed):
    rng = random.Random(seed)
    return " ".join(f"{rng.choice(PALABRAS)}t{seed}x{i}" for i in range(palabras))


def test_t07_114_a_escala_el_par_entre_familias_se_agrupa_con_plantilla_comun():
    """#114 a escala: 10^3 casos de 10 familias con una plantilla comun (boilerplate de verdad) y un par
    bench/train casi identico entre familias -> agrupado; nada mas se agrupa."""
    rng = random.Random(1140)
    plantilla = _plantilla(150, 1)
    docs = [(f"geo-f{i % 10}.c{i:04d}@v001", f"f{i % 10}", plantilla + " " + _frase(rng, 30)) for i in range(998)]
    base = _peticion_21(rng)
    docs += [("geo-bench.par@v001", "bench", plantilla + " " + base + " alfa"),
             ("geo-f3.par@v001", "f3", plantilla + " " + base + " beta")]
    r = dd.agrupar(docs)
    assert r["boilerplate"] > 0
    assert _grupos(r) == [["geo-bench.par@v001", "geo-f3.par@v001"]]


def test_t07_plantilla_del_90_por_ciento_no_da_falsos_positivos_y_avisa():
    """Revision previa de D-f3 (§2, Critical): 10^3 casos de 10 familias con 90 % de plantilla y 10 %
    propio -> 0 grupos (el rescate sobre el conjunto original lo agrupaba todo) y un aviso por caso que
    conserva < 20 % de sus shingles (H2: se ve, no decide)."""
    rng = random.Random(90)
    plantilla = _plantilla(270, 2)
    docs = [(f"geo-f{i % 10}.c{i:04d}@v001", f"f{i % 10}", plantilla + " " + _frase(rng, 30)) for i in range(1000)]
    r = dd.agrupar(docs)
    assert _grupos(r) == []
    assert len(r["avisos"]) == 1000
    assert all("near-duplicate no evaluable sobre la plantilla" in a["motivo"] for a in r["avisos"])
    assert [a["id"] for a in r["avisos"]] == sorted(d[0] for d in docs)


def test_t07_aviso_solo_si_conserva_menos_del_20_por_ciento():
    rng = random.Random(21)
    plantilla = _plantilla(60, 3)
    docs = [(f"c{i:02d}@v001", f"f{i}", plantilla + " " + _frase(rng, 30)) for i in range(20)]
    docs.append(("poco@v001", "fz", plantilla + " " + _frase(rng, 5)))
    r = dd.agrupar(docs)
    assert [a["id"] for a in r["avisos"]] == ["poco@v001"]


def test_t07_caso_todo_boilerplate_solo_agrupa_con_su_identico():
    docs = _con_boilerplate()
    mitad = " ".join(SISTEMA.split()[:60])
    docs += [("geo-vacio.a@v001", "va", SISTEMA), ("geo-vacio.b@v001", "vb", SISTEMA),
             ("geo-vacio.c@v001", "vc", mitad)]
    r = dd.agrupar(docs)
    # H3: el colapso de exactos es por IGUALDAD del conjunto ORIGINAL, nunca del filtrado (los tres
    # quedan vacios al filtrar; `c` tiene otro original y no se agrupa)
    assert _grupos(r) == [["geo-vacio.a@v001", "geo-vacio.b@v001"]]


# ------------------------------------------------------------------ exactitud del filtro de prefijo

def _fuerza_bruta(docs, umbral, ventana, fraccion):
    """Referencia O(n^2): mismos shingles filtrados que `agrupar`, todos los pares."""
    conjuntos, originales = dd._conjuntos(docs, ventana, fraccion)[:2]
    padre = list(range(len(docs)))

    def find(x):
        while padre[x] != x:
            x = padre[x]
        return x
    for i, j in itertools.combinations(range(len(docs)), 2):
        si, sj = conjuntos[i], conjuntos[j]
        if (si and sj and dd._supera(len(si & sj), len(si | sj), dd._fraccion(umbral))) \
                or originales[i] == originales[j]:
            padre[find(i)] = find(j)
    comp = {}
    for i in range(len(docs)):
        comp.setdefault(find(i), []).append(docs[i][0])
    return sorted(sorted(g) for g in comp.values() if len(g) > 1)


def _corpus_aleatorio(umbral, n=60):
    rng = random.Random(int(umbral * 100))
    docs = []
    for i in range(n):
        base = _frase(rng, rng.randrange(3, 25))
        docs.append((f"c{i:02d}@v001", f"f{i % 7}", base))
        if rng.random() < 0.5:
            mut = base.split()
            for _ in range(rng.randrange(0, 4)):
                mut[rng.randrange(len(mut))] = rng.choice(PALABRAS)
            docs.append((f"c{i:02d}@v002", f"f{i % 7}", " ".join(mut)))
    return docs


@pytest.mark.parametrize("umbral", [0.3, 0.5, 0.7, 0.8, 0.9, 1.0])
def test_t07_el_filtro_de_prefijo_da_lo_mismo_que_todos_los_pares(umbral):
    docs = _corpus_aleatorio(umbral)
    r = dd.agrupar(docs, umbral=umbral, ventana=2, fraccion_boilerplate=1.0)
    # los componentes del filtro no tienen singletons; la referencia tampoco
    assert _grupos(r) == _fuerza_bruta(docs, umbral, 2, 1.0)


@pytest.mark.parametrize("umbral", [0.5, 0.7, 0.8, 0.9])
def test_t07_mid_prefix_y_filtro_posicional_dan_lo_mismo_que_la_fuerza_bruta(umbral):
    """H3: indice solo del mid-prefix PPJoin + sondeo con el prefijo completo + filtro posicional y de
    longitud = fuerza bruta, tambien con el filtro de boilerplate activo y ante permutaciones."""
    for semilla in range(8):
        rng = random.Random(semilla * 31 + int(umbral * 10))
        comun = _frase(rng, 12)
        docs = []
        for i in range(40):
            base = (comun + " " if rng.random() < 0.7 else "") + _frase(rng, rng.randrange(2, 14))
            docs.append((f"s{semilla}c{i:02d}@v001", f"f{i % 5}", base))
            for v in range(2, 2 + rng.randrange(0, 3)):
                mut = base.split()
                for _ in range(rng.randrange(0, 3)):
                    mut[rng.randrange(len(mut))] = rng.choice(PALABRAS)
                docs.append((f"s{semilla}c{i:02d}@v{v:03d}", f"f{i % 5}", " ".join(mut)))
        esperado = _fuerza_bruta(docs, umbral, 1, 0.5)
        for p in range(3):
            barajado = list(docs)
            random.Random(p).shuffle(barajado)
            assert _grupos(dd.agrupar(barajado, umbral=umbral, ventana=1)) == esperado, (umbral, semilla, p)


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


def _115a(n):
    """#115a: DOS familias con el mismo prompt de sistema (~82 % de los shingles de cada caso: entraba
    en todos los prefijos porque la regla «>= 3 familias» apagaba el filtro)."""
    rng = random.Random(1151)
    sistema = _plantilla(100, 5)
    return [(f"c{i:05d}@v001", f"f{i % 2}", sistema + " " + _frase(rng, 22)) for i in range(n)]


def _115b(n):
    """#115b: dos plantillas, cada una en el 49 % de los casos (no llegan a boilerplate), y un texto
    propio corto (~17 % de los shingles del caso): con el prefijo de siempre entraban en todos."""
    rng = random.Random(1152)
    x, y = _plantilla(100, 6), _plantilla(100, 7)
    docs = []
    for i in range(n):
        t = x if i % 100 < 49 else y if i % 100 < 98 else ""
        docs.append((f"c{i:05d}@v001", f"f{i % 10}", (t + " " if t else "") + _frase(rng, 22)))
    return docs


@pytest.mark.parametrize("corpus", [_115a, _115b])
def test_t07_115_texto_comun_bajo_el_umbral_no_escanea_el_indice(corpus):
    """#115 (a) y (b) a 3 000 casos: 0 escaneos del indice y 0 pares verificados (antes, n(n-1)/2)."""
    r = dd.agrupar(corpus(3000))
    assert _grupos(r) == []
    assert r["escaneos_indice"] == 0, r["escaneos_indice"]
    assert r["pares_verificados"] == 0, r["pares_verificados"]


def test_t07_escaneos_solo_dentro_de_grupos_que_son_near_duplicates():
    """Peor caso declarado de H3: O(m^2) escaneos solo dentro de un grupo de m near-duplicates."""
    rng = random.Random(3)
    base = _frase(rng, 40)
    docs = [(f"g@v{v:03d}", "g", base + f" cambio{v} otro{v}") for v in range(1, 31)]
    docs += [(f"r{i:03d}@v001", f"f{i % 9}", _frase(rng, 40)) for i in range(300)]
    r = dd.agrupar(docs, umbral=0.8)
    assert _grupos(r) == [[f"g@v{v:03d}" for v in range(1, 31)]]
    assert 0 < r["escaneos_indice"] <= 30 * 30 * 40, r["escaneos_indice"]


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


# ------------------------------------------------------------------ H4: muestreo por valor

def test_t07_bajo_el_presupuesto_el_jaccard_es_exacto():
    r = dd.agrupar(_con_boilerplate())
    assert r["jaccard"] == "exacto" and r["muestreo"]["r"] == 1.0
    assert r["muestreo"]["presupuesto"] == dd.PRESUPUESTO_DEFECTO == 10 ** 7


def test_t07_shingle_es_un_entero_de_64_bits_determinista():
    import hashlib
    h = dd.hash_shingle("uno\ndos\ntres")
    assert h == int.from_bytes(hashlib.blake2b("uno\ndos\ntres".encode("utf-8"), digest_size=8).digest(), "little")
    assert 0 <= h < 2 ** 64


def test_t07_muestreo_global_independiente_del_orden():
    """`r = min(1, B / suma |A_i|)` GLOBAL: el mismo conjunto muestreado sea cual sea el orden de
    entrada (una poda con la `r` parcial dependeria del orden)."""
    docs = _corpus_aleatorio(0.5, n=80)
    salidas = set()
    for semilla in range(6):
        barajado = list(docs)
        random.Random(semilla).shuffle(barajado)
        r = dd.agrupar(barajado, umbral=0.5, ventana=1, fraccion_boilerplate=1.0, presupuesto=150)
        salidas.add(json.dumps(r, sort_keys=True))
    assert len(salidas) == 1
    r = json.loads(salidas.pop())
    assert r["jaccard"] == "muestreado" and 0 < r["muestreo"]["r"] < 1
    assert r["muestreo"]["shingles"] > 150


def test_t07_muestreo_conserva_solo_hashes_bajo_el_limite():
    docs = _corpus_aleatorio(0.7, n=80)
    acc = dd.Acumulador(ventana=1, presupuesto=100)
    for d in docs:
        acc.anadir(*d)
    total = acc.shingles_totales
    limite = -(-(100 << 64) // total)
    muestras = acc.muestras()
    assert sum(len(m) for m in muestras.values()) < total
    for i, _fam, texto in docs:
        completo = {dd.hash_shingle(s) for s in dd.shingles_de(texto, 1)}
        assert set(muestras[i]) == {h for h in completo if h < limite}


def test_t07_caso_sin_muestras_avisa_y_no_se_agrupa_con_otro_sin_muestras():
    """Con `r < 1` un caso pequeño puede quedarse sin muestras: nunca se agrupa por tener el conjunto
    muestreado VACIO igual que otro (el colapso de exactos usa la huella del conjunto completo)."""
    rng = random.Random(4)
    docs = [(f"c{i:03d}@v001", f"f{i % 5}", _frase(rng, 200)) for i in range(20)]
    docs += [(f"p{i}@v001", "p", f"palabra{i}") for i in range(30)]
    r = dd.agrupar(docs, ventana=1, presupuesto=200)
    assert r["jaccard"] == "muestreado"
    vacios = [a["id"] for a in r["avisos"] if "sin shingles muestreados" in a["motivo"]]
    assert vacios, r["avisos"]
    assert not any(g for g in r["grupos"] if set(g) & set(vacios))


def test_t07_el_texto_no_se_guarda():
    """H4: el texto se descarta al shinglearlo; el acumulador guarda enteros de 64 bits (`array('Q')`)."""
    acc = dd.Acumulador(ventana=3)
    acc.anadir("a@v001", "f", "uno dos tres cuatro cinco seis")
    assert not any(isinstance(v, str) and "cuatro" in v for v in vars(acc).values())
    (m,) = acc.muestras().values()
    assert m.typecode == "Q"


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


# ------------------------------------------------------------------ fix2 de la Fase 3 (#141, #142, #144, #145, #146)

def _casi_iguales(m, palabras, seed):
    """m casos casi iguales (1 % de palabras cambiadas) de UNA familia + m de relleno aleatorio: el
    grupo es la mitad justa del corpus, asi que no llega a boilerplate (`df > 0.5·n` estricto)."""
    rng = random.Random(seed)
    base = [f"w{rng.randrange(20000)}" for _ in range(palabras)]
    docs = []
    for i in range(m):
        ws = list(base)
        for _ in range(max(1, palabras // 100)):
            ws[rng.randrange(palabras)] = f"w{rng.randrange(20000)}"
        docs.append((f"g{i:04d}@v001", "g", " ".join(ws)))
    docs += [(f"r{i:04d}@v001", f"r{i}", " ".join(f"w{rng.randrange(20000)}" for _ in range(palabras)))
             for i in range(m)]
    return docs


def test_t07_141_grupo_de_casi_iguales_escanea_en_lineal_no_en_m_cuadrado():
    """#141: dentro de un grupo de m near-duplicates reales se escaneaba el mid-prefix de todos contra
    todos (O(m^2 · |x|)): con cubos por componente, un cubo ya unido a x se salta entero."""
    m = 120
    r = dd.agrupar(_casi_iguales(m, 200, 141))
    assert _grupos(r) == [[f"g{i:04d}@v001" for i in range(m)]]
    assert r["escaneos_indice"] <= 20 * m, r["escaneos_indice"]      # antes: ~2,5·10^5
    assert r["pares_verificados"] <= 2 * m, r["pares_verificados"]


def test_t07_141_con_cubos_grandes_sigue_igual_que_la_fuerza_bruta():
    """#141: la verificacion adelantada de un cubo grande y el salto de cubos no pierden ningun par:
    grupos de 12-20 casi iguales (cubos > CUBO_VERIFICACION) mezclados con ruido."""
    for semilla in range(4):
        rng = random.Random(1410 + semilla)
        docs = []
        for g in range(4):
            base = _frase(rng, 14)
            for v in range(rng.randrange(12, 21)):
                mut = base.split()
                for _ in range(rng.randrange(0, 3)):
                    mut[rng.randrange(len(mut))] = rng.choice(PALABRAS)
                docs.append((f"s{semilla}g{g}v{v:02d}", f"f{g}", " ".join(mut)))
        docs += [(f"s{semilla}r{i:02d}", f"r{i}", _frase(rng, rng.randrange(4, 16))) for i in range(40)]
        for umbral in (0.5, 0.7, 0.8):
            esperado = _fuerza_bruta(docs, umbral, 1, 1.0)
            assert any(len(g) > dd.CUBO_VERIFICACION for g in esperado), "el corpus no ejercita los cubos grandes"
            assert _grupos(dd.agrupar(docs, umbral=umbral, ventana=1, fraccion_boilerplate=1.0)) == esperado


def test_t07_142_frecuencias_por_elemento_sin_dict_de_todo_el_corpus():
    """#142: la df se guarda como un `array('I')` por caso alineado con su muestra (4 B por shingle),
    no en un dict {hash: df} de todos los shingles con df >= 2 (~100 B cada uno)."""
    from array import array
    from collections import Counter
    rng = random.Random(142)
    arrays = [array("Q", sorted({rng.randrange(1 << 64) for _ in range(rng.randrange(0, 30))} | {7, 9}))
              for _ in range(50)] + [None, array("Q")]
    ref = Counter(h for a in arrays if a for h in a)
    dfs, hist = dd._frecuencias(arrays)
    assert len(dfs) == len(arrays)
    for a, d in zip(arrays, dfs):
        assert isinstance(d, array) and d.typecode == "I"
        assert list(d) == [ref[h] for h in (a or ())]
    assert hist == Counter(ref.values())


def test_t07_142_memoria_del_dedup_en_pares_casi_iguales():
    """#142: pares v001/v002 casi iguales (casi todos los shingles con df >= 2). Con el dict global de
    df, el pico era 84 B por shingle (Windows, `tracemalloc`); ahora 64: la muestra + la df por
    elemento + un tramo de conteo (con 10^4 x 1 000 palabras, 421 -> ver la Evidencia de #142)."""
    import tracemalloc
    rng = random.Random(1420)
    docs = []
    for i in range(1000):
        a = [f"w{rng.randrange(50000)}" for _ in range(200)]
        b = list(a)
        b[rng.randrange(200)] = "cambio"
        docs += [(f"c{i:04d}@v001", f"f{i}", " ".join(a)), (f"c{i:04d}@v002", f"f{i}", " ".join(b))]
    acc = dd.Acumulador()
    for d in docs:
        acc.anadir(*d)
    total = acc.shingles_totales
    tracemalloc.start()
    antes = tracemalloc.get_traced_memory()[0]
    r = acc.agrupar()
    pico = tracemalloc.get_traced_memory()[1] - antes
    tracemalloc.stop()
    assert len(r["grupos"]) == 1000
    assert pico / total < 72, pico / total                          # antes: 84 B por shingle


def test_t07_144_tramos_adaptativos():
    """#144: un solo tramo si el conteo cabe en el presupuesto de conteo (antes, 64 tramos por encima
    de 2^18 shingles: O(tramos · n) con 10^5 casos pequeños); mas, solo si no cabe."""
    assert dd.CONTEO_MAX_TRAMO >= 1 << 21
    assert dd._tramos(0) == dd._tramos(1) == dd._tramos(dd.CONTEO_MAX_TRAMO) == 1
    assert dd._tramos(dd.CONTEO_MAX_TRAMO + 1) == 2
    assert dd._tramos(10 ** 7) == 8                                 # antes: 64
    assert dd._tramos(10 ** 12) == 256


def test_t07_144_varios_tramos_cuentan_lo_mismo_que_uno(monkeypatch):
    from array import array
    from collections import Counter
    rng = random.Random(144)
    arrays = [array("Q", sorted({rng.randrange(1 << 64) for _ in range(40)} | {5, (1 << 63) + 1}))
              for _ in range(60)]
    uno = dd._frecuencias(arrays)
    monkeypatch.setattr(dd, "CONTEO_MAX_TRAMO", 64)
    assert dd._tramos(sum(map(len, arrays))) > 16
    varios = dd._frecuencias(arrays)
    assert [list(d) for d in varios[0]] == [list(d) for d in uno[0]] and varios[1] == uno[1]
    assert uno[1] == Counter(Counter(h for a in arrays for h in a).values())


def _pares_145(n_pares, inter, en_benchmark):
    """#145: pares de conjuntos de 1 000 shingles (ventana 1, palabras unicas) con `inter` en comun:
    Jaccard real `inter / (2000 - inter)`. El segundo de cada par va a benchmark si `en_benchmark`."""
    docs, bench = [], set()
    for p in range(n_pares):
        a = [f"p{p}a{i}" for i in range(1000)]
        b = a[:inter] + [f"p{p}b{i}" for i in range(1000 - inter)]
        docs += [(f"t{p:03d}@v001", f"t{p}", " ".join(a)), (f"b{p:03d}@v001", f"b{p}", " ".join(b))]
        if en_benchmark:
            bench.add(f"b{p:03d}@v001")
    return docs, bench


def test_t07_145_escenario_literal_cruce_conservador_con_r_de_un_decimo():
    """#145 (Z-B1): 200 pares de 1 000 shingles, umbral 0.8, r = 0.1, Jaccard real 0.82: con el umbral
    sobre la muestra solo se agrupaba ~2/3; el cruce train/benchmark usa `umbral - margen` y lo ve."""
    docs, bench = _pares_145(200, 901, True)                        # J real = 901/1099 = 0.8198
    r = dd.agrupar(docs, umbral=0.8, ventana=1, fraccion_boilerplate=1.0, presupuesto=40000, benchmark_ids=bench)
    assert r["jaccard"] == "muestreado" and abs(r["muestreo"]["r"] - 0.1) < 1e-12
    agrupados = sum(1 for g in r["grupos"] if len(g) == 2)
    assert agrupados < 190, agrupados                                # el umbral sobre la muestra pierde pares
    cruzados = {t for t, _b in r["cruces"]}
    assert len(cruzados) >= 195, len(cruzados)
    assert all(t.startswith("t") and b.startswith("b") and t[1:] == b[1:] for t, b in r["cruces"])
    assert r["cruce"] == {"criterio": "conservador", "z": 2.0, "margen_max": 0.2, "umbral_minimo": 0.6,
                          "margen": "z*sqrt(J(1-J)/k), k = shingles muestreados de la union del par"}


def test_t07_145_el_criterio_conservador_solo_aplica_al_cruce():
    """#145: J real 0.78 dentro de UNA particion (ninguno en benchmark): los grupos siguen con el umbral
    (~59/200 de mas, no mas) y no hay cruces; los mismos pares cruzando particion, casi todos marcados."""
    docs, _ = _pares_145(200, 876, False)                           # J real = 876/1124 = 0.7794
    r = dd.agrupar(docs, umbral=0.8, ventana=1, fraccion_boilerplate=1.0, presupuesto=40000, benchmark_ids=set())
    assert r["cruces"] == []
    assert sum(1 for g in r["grupos"] if len(g) == 2) < 100
    docs, bench = _pares_145(200, 876, True)
    r2 = dd.agrupar(docs, umbral=0.8, ventana=1, fraccion_boilerplate=1.0, presupuesto=40000, benchmark_ids=bench)
    assert r2["grupos"] == r["grupos"]                               # los grupos no cambian
    assert len(r2["cruces"]) >= 150, len(r2["cruces"])


def test_t07_145_con_jaccard_exacto_no_hay_criterio_conservador():
    docs, bench = _pares_145(20, 901, True)
    r = dd.agrupar(docs, umbral=0.8, ventana=1, fraccion_boilerplate=1.0, benchmark_ids=bench)
    assert r["jaccard"] == "exacto" and r["cruces"] == [] and r["cruce"] == {"criterio": "umbral"}
    assert len(r["grupos"]) == 20
    sin = dd.agrupar(docs, umbral=0.8, ventana=1, fraccion_boilerplate=1.0, presupuesto=4000)
    assert sin["cruces"] == [] and sin["cruce"] == {"criterio": "umbral"}   # sin benchmark declarado


def test_t07_145_margen_de_la_estimacion():
    assert dd._margen_cruce(0.8, 110) == pytest.approx(2 * (0.8 * 0.2 / 110) ** 0.5)
    assert dd._margen_cruce(0.8, 1) == pytest.approx(0.2)            # acotado
    assert dd._margen_cruce(0.3, 1) == pytest.approx(0.15)           # nunca mas de umbral/2
    assert dd._umbral_cruce(0.8) == dd._fraccion(0.8) - dd.MARGEN_MAX_CRUCE


def test_t07_145_duplicados_exactos_de_train_se_marcan_todos():
    docs, bench = _pares_145(3, 901, True)
    docs.append(("t000@v002", "t0", docs[0][2]))                    # copia exacta del de train
    r = dd.agrupar(docs, umbral=0.8, ventana=1, fraccion_boilerplate=1.0, presupuesto=600, benchmark_ids=bench)
    marcados = {t for t, _b in r["cruces"]}
    assert marcados and ("t000@v001" in marcados) == ("t000@v002" in marcados)


def test_t07_146_las_copias_exactas_heredan_el_aviso_de_su_representante():
    """#146: el aviso H2 de un caso casi todo plantilla lo llevan tambien sus copias exactas (mismo
    conjunto), no solo el representante (el de id menor)."""
    rng = random.Random(146)
    plantilla = _plantilla(60, 4)
    docs = [(f"c{i:02d}@v001", f"f{i}", plantilla + " " + _frase(rng, 30)) for i in range(20)]
    poco = plantilla + " " + _frase(rng, 5)
    docs += [("poco@v001", "fz", poco), ("poco@v002", "fz", poco)]
    r = dd.agrupar(docs)
    assert [a["id"] for a in r["avisos"]] == ["poco@v001", "poco@v002"]
    assert ["poco@v001", "poco@v002"] in r["grupos"]


def _corpus_cubos(seed):
    """#141: 1-3 grupos de 9-13 casi iguales sobre un vocabulario pequeño (cubos > CUBO_VERIFICACION,
    que se verifican por adelantado y se saltan) + casos sueltos que comparten palabras con ellos."""
    rng = random.Random(seed)
    voc = [f"v{i}" for i in range(rng.randrange(8, 30))]
    docs = []
    for g in range(rng.randrange(1, 4)):
        base = rng.sample(voc, rng.randrange(3, 8))
        for k in range(rng.randrange(9, 14)):
            ws = list(base)
            if rng.random() < 0.5:
                ws[rng.randrange(len(ws))] = rng.choice(voc)
            if rng.random() < 0.3:
                ws.append(rng.choice(voc))
            docs.append((f"g{g}k{k:02d}", f"f{g}", " ".join(ws)))
    for i in range(rng.randrange(3, 15)):
        docs.append((f"z{i:02d}", f"z{i}", " ".join(rng.sample(voc, rng.randrange(2, 8)))))
    return docs


@pytest.mark.parametrize("seed", [5, 198] + list(range(30)))
def test_t07_141_cubos_por_componente_igual_que_la_fuerza_bruta(seed):
    """#141: un cubo del indice solo tiene casos de UNA componente (si se mezclaran, saltarlo perderia
    un par: semilla 198) y la verificacion adelantada de un cubo grande solo une si el par supera el
    umbral (semilla 5)."""
    docs = _corpus_cubos(seed)
    for umbral in (0.5, 0.6, 0.7, 0.8):
        assert _grupos(dd.agrupar(docs, umbral=umbral, ventana=1, fraccion_boilerplate=1.0)) == \
            _fuerza_bruta(docs, umbral, 1, 1.0), (seed, umbral)


# ------------------------------------------------------------------ T-10 fix2 #178: CLI EN PROCESO

def test_t10fix2_178_cli_de_dedup_en_proceso(tmp_path, capsys):
    """#178: `dedup.main([...])` en proceso: texto, `--json`, avisos, y cada error de uso (exit 2)."""
    docs = tmp_path / "docs.jsonl"
    texto = "genera una rampa de treinta grados con una bola roja que rueda sin salirse"
    docs.write_text("".join(json.dumps({"id": f"c{i}", "family": "f", "text": texto}) + "\n" for i in range(3))
                    + "\n" + json.dumps({"id": "c\u00e9", "family": "g", "text": "ok"}) + "\n", encoding="utf-8")
    assert dd.main([str(docs)]) == 0
    salida = capsys.readouterr()
    assert "grupo: " in salida.out and "grupo(s) de near-duplicates" in salida.out
    assert dd.main([str(docs), "--json"]) == 0 and json.loads(capsys.readouterr().out)["grupos"]
    assert dd.main([str(docs), "--presupuesto", "3"]) == 0 and "r = " in capsys.readouterr().out
    for contenido in ("{roto\n", "[1, 2]\n", json.dumps({"id": 1, "family": "f", "text": "x"}) + "\n"):
        malo = tmp_path / "malo.jsonl"
        malo.write_text(contenido, encoding="utf-8")
        assert dd.main([str(malo)]) == 2 and "linea 1" in capsys.readouterr().err
    (tmp_path / "latin1.jsonl").write_bytes(b"\xff\xfe\n")
    assert dd.main([str(tmp_path / "latin1.jsonl")]) == 2 and "UTF-8" in capsys.readouterr().err
    assert dd.main([str(tmp_path / "no-existe.jsonl")]) == 2
    assert dd.main([str(docs), "--ventana", "0"]) == 2
    with pytest.raises(ValueError):
        dd.agrupar([("a", "f")])
    with pytest.raises(ValueError):
        dd._validar_parametros(3, 0.0, 10)
    with pytest.raises(ValueError):
        dd._validar_parametros(3, 0.5, 0)


def _code_health():
    ruta = os.path.join(HERE, "..", "..", "code-health", "scripts", "code-health.py")
    spec = importlib.util.spec_from_file_location("code_health_178", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_t10fix2_178_cli_de_code_health_en_proceso(tmp_path, capsys):
    """#178: el CLI de `code-health.py` (canonico de `shingles`, T-07) en proceso: ruta inexistente,
    baseline ilegible o que no es un informe (exit 2), informe en Markdown y en JSON y con baseline."""
    ch = _code_health()
    (tmp_path / "a.py").write_text("def f(x):\n    # TODO: revisar\n    return x + 1\n" * 3, encoding="utf-8")
    assert ch.main([str(tmp_path / "no-existe")]) == 2
    (tmp_path / "base.json").write_text("[]", encoding="utf-8")
    assert ch.main([str(tmp_path), "--baseline", str(tmp_path / "base.json")]) == 2
    assert ch.main([str(tmp_path), "--baseline", str(tmp_path / "no.json")]) == 2
    capsys.readouterr()
    assert ch.main([str(tmp_path)]) == 0 and "TODO/FIXME" in capsys.readouterr().out
    assert ch.main([str(tmp_path), "--json"]) == 0
    informe = capsys.readouterr().out
    (tmp_path / "prev.json").write_text(informe, encoding="utf-8")
    assert ch.main([str(tmp_path), "--baseline", str(tmp_path / "prev.json"), "--exclude-tests"]) == 0
