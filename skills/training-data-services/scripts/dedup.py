#!/usr/bin/env python3
"""
dedup.py — near-duplicates DETERMINISTAS entre casos de `training-data-services` (T-07, CA-10).

Sin embeddings, sin modelo y sin red (mismo criterio que ADR-013): la tecnica de shingles/Jaccard de
`skills/code-health/scripts/code-health.py` aplicada al CONTENIDO VARIABLE de cada caso (peticion +
contexto + trayectoria; ni restricciones, ni metricas, ni marcas de tiempo). La funcion `shingles`
es una COPIA DECLARADA del canonico de code-health (centinelas `# --8<--`, registro
`agent-kits/shared/copias.json`, test de identidad `tests/test_copias_declaradas.py`, ADR-016): las
skills son standalone y no se importan entre si. La normalizacion NO se copia: la de code-health
colapsa identificadores y numeros (`id`/`num`), util para codigo e inutil para lenguaje natural;
aqui un token es una palabra `\\w+` en minusculas (`casefold`), numeros incluidos.

`agrupar(documentos, umbral, ventana, fraccion_boilerplate, presupuesto)` — `documentos`: iterable de
`(id, family, texto)` (ids unicos; puede ser un generador: cada texto se descarta al shinglearlo).
Devuelve los GRUPOS de near-duplicates (componentes conexas del grafo «Jaccard >= umbral»),
deterministas: cada grupo ordenado por id y los grupos por su primer id. `Acumulador` es la misma
maquina en streaming (`anadir(id, family, texto)` y despues `agrupar(umbral, fraccion)`): el
ensamblador la alimenta caso a caso sin guardar ningun texto (fix1, H4/H5).
  - Shingles: `ventana` palabras consecutivas (un texto mas corto que la ventana es UN shingle con
    todas sus palabras); cada shingle es un ENTERO de 64 bits (`blake2b(digest_size=8)`,
    `int.from_bytes(…, "little")`: el mismo en todos los procesos y sistemas), nunca un `str`.
    Jaccard = |A ∩ B| / |A ∪ B| con ENTEROS y el umbral como fraccion exacta
    (`Fraction(repr(umbral))`: 0.7 * 10 no es 7.000000000000001).
  - MUESTREO POR VALOR (H4): se conserva el shingle `h` si `h < r · 2^64`, con
    `r = min(1, presupuesto / suma |A_i|)` GLOBAL (la suma de los tamaños de TODOS los casos: la
    muestra no depende del orden de entrada; mientras llega el corpus se poda con el limite vigente,
    que solo baja). Los conjuntos muestreados son conjuntos de verdad: frecuencia documental,
    boilerplate, prefijo, filtro posicional y Jaccard son EXACTOS sobre la muestra. Con
    `suma |A_i| <= presupuesto` (10^7 por defecto, ~60 MiB de texto) `r = 1` y todo es exacto
    (`jaccard: "exacto"`); si no, `jaccard: "muestreado"` y la salida declara `r`. Limite declarado:
    con `r < 1` un caso pequeño queda con pocas muestras (o ninguna: aviso «sin shingles
    muestreados»; entonces solo se agrupa con un duplicado EXACTO). En memoria: un `array('Q')` por
    caso y, al agrupar, la frecuencia documental exacta contada por tramos del espacio de hashes (solo
    se guarda la de los shingles con df >= 2; los de df == 1 nunca coinciden con otro caso y ni se
    indexan ni se sondean).
  - BOILERPLATE (H1; texto fijo repetido: prompt de sistema, plantillas): un shingle presente en MAS
    de `fraccion_boilerplate` de los casos (0.5; frecuencia documental, estricta) se ignora, pero
    solo con al menos `N_MIN_BOILERPLATE` (20) casos: por debajo no se filtra nada (#114: con 4
    casos, lo que comparten dos near-duplicates entre familias no es plantilla). Sin condicion de
    familias (#115a: dos familias con el mismo prompt de sistema). Limite declarado: un bloque en mas
    de la mitad de los casos es plantilla por definicion, aunque sean versiones de una sola familia.
    `fraccion_boilerplate=1.0` desactiva el filtro.
  - AVISO (H2: se ve, no decide): un caso que conserva menos del 20 % de sus shingles (muestreados)
    tras quitar el boilerplate -> `{"id", "motivo": "near-duplicate no evaluable sobre la plantilla…"}`
    en `avisos`. Se compara igual, con lo que queda (un rescate sobre el conjunto original agrupaba
    todo un corpus con plantilla larga: revision previa de D-f3, §2 eliminado).
  - DUPLICADOS EXACTOS (H3): se colapsan ANTES de comparar, por IGUALDAD del conjunto ORIGINAL (sin
    filtrar): huella `blake2b` de 128 bits del conjunto completo + igualdad de la muestra; nunca por
    el filtrado (dos casos todo-plantilla distintos no son el mismo). 1 000 copias identicas cuestan
    1 000 huellas y 0 pares.
  - ESCALA (H3, PPJoin): orden global por frecuencia documental ascendente (desempate por el hash);
    los casos se procesan por tamaño (y id); cada uno SONDEA el indice con su prefijo completo
    `|x| - ceil(t·|x|) + 1` y despues INDEXA solo su mid-prefix `|x| - ceil(2t/(1+t)·|x|) + 1`, con
    filtro de longitud (`t·|x| <= |y|`) y posicional (lo que queda de ambos detras de la coincidencia
    tiene que poder llegar al solapamiento minimo `ceil(t/(1+t)·(|x|+|y|))`). Exacto: ningun par con
    Jaccard >= t se pierde. Peor caso declarado: O(m^2) escaneos solo DENTRO de un grupo de m casos
    que SON near-duplicates entre si; el texto comun que no llega a boilerplate (#115b) queda al final
    del orden y no entra en el mid-prefix de nadie: 0 escaneos.
  - `escaneos_indice` y `pares_verificados` hacen visible el trabajo real (tests de escala); `avisos`,
    `jaccard` y `muestreo` (`r`, `presupuesto`, `shingles`) declaran la exactitud.

`texto_de_caso(caso)` — el texto variable de un caso (dict con `request`, `context`, `trajectory`):
objetos serializados con claves ordenadas (el orden de claves no cambia el texto).

Uso (exit 0 ok · 2 uso, fichero ausente o JSONL ilegible; nunca un traceback):
  dedup.py <documentos.jsonl> [--umbral 0.8] [--ventana 3] [--boilerplate 0.5] [--presupuesto 10000000] [--json]
  (una linea JSON por documento: {"id": "...", "family": "...", "text": "..."})
"""
import argparse
import hashlib
import json
import math
import re
import sys
from array import array
from bisect import bisect_left
from collections import Counter, defaultdict
from fractions import Fraction

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

UMBRAL_DEFECTO = 0.8
VENTANA_DEFECTO = 3
BOILERPLATE_DEFECTO = 0.5
N_MIN_BOILERPLATE = 20             # H1: por debajo, ningun shingle es plantilla
PRESUPUESTO_DEFECTO = 10 ** 7      # H4: shingles muestreados en total (por debajo, r = 1: exacto)
FRACCION_AVISO = Fraction(1, 5)    # H2: aviso si un caso conserva < 20 % tras quitar la plantilla
AVISO_PLANTILLA = ("near-duplicate no evaluable sobre la plantilla: conserva {k} de {n} shingles tras quitar "
                   "el boilerplate (< 20 %); se compara con lo que queda")
AVISO_SIN_MUESTRAS = ("sin shingles muestreados (r < 1 y caso pequeño): solo se agrupa con un duplicado exacto; "
                      "sube el presupuesto de muestreo para compararlo")
_PALABRA = re.compile(r"\w+")


# --8<-- shingles (ventana deslizante) COMPARTIDOS -- REPLICADO LITERAL en skills/code-health/scripts/code-health.py (canonico) y skills/training-data-services/scripts/dedup.py (ADR-016)
def shingles(unidades, window):
    """Shingles de `window` unidades consecutivas (lineas normalizadas, palabras...), en orden, como
    la PROPIA cadena unida por `\\n` (nunca `hash()`: determinista entre procesos, PYTHONHASHSEED)."""
    return ["\n".join(unidades[k:k + window]) for k in range(len(unidades) - window + 1)]
# --8<-- fin shingles (ventana deslizante) COMPARTIDOS


def tokens(texto):
    """Palabras `\\w+` en minusculas (`casefold`), numeros incluidos."""
    return _PALABRA.findall(texto.casefold())


def shingles_de(texto, ventana=VENTANA_DEFECTO):
    """Conjunto de shingles de un texto; mas corto que la ventana -> un shingle con todo."""
    ts = tokens(texto)
    return set(shingles(ts, min(ventana, len(ts)))) if ts else set()


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a or b) else 0.0


def _plano(v):
    return v if isinstance(v, str) else json.dumps(v, sort_keys=True, ensure_ascii=False, allow_nan=False)


def texto_de_caso(caso):
    """Contenido VARIABLE del caso: peticion + contexto + trayectoria (rol, contenido, nombre de la
    herramienta y `tool_calls` con sus argumentos). Fuera: restricciones, metricas, `ts`."""
    partes = []
    for clave in ("request", "context"):
        v = caso.get(clave)
        if v is not None:
            partes.append(_plano(v))
    for turno in caso.get("trajectory") or ():
        if not isinstance(turno, dict):
            continue
        for clave in ("role", "name", "content"):
            v = turno.get(clave)
            if isinstance(v, str):
                partes.append(v)
        for call in turno.get("tool_calls") or ():
            if isinstance(call, dict):
                partes.append(_plano(call.get("name", "")))
                if "arguments" in call:
                    partes.append(_plano(call["arguments"]))
    return "\n".join(partes)


def hash_shingle(sh):
    """Un shingle como entero de 64 bits, determinista entre procesos y sistemas (H4)."""
    return int.from_bytes(hashlib.blake2b(sh.encode("utf-8"), digest_size=8).digest(), "little")


def _fraccion(umbral):
    """El umbral como fraccion EXACTA en (0, 1]; si no, `ValueError`."""
    if isinstance(umbral, bool) or not isinstance(umbral, (int, float)) or math.isnan(umbral) \
            or not 0 < umbral <= 1:
        raise ValueError(f"umbral de Jaccard fuera de (0, 1]: {umbral!r}")
    return Fraction(repr(float(umbral)))


def _supera(inter, union, t):
    """Jaccard >= t con enteros: inter / union >= num / den."""
    return union > 0 and inter * t.denominator >= t.numerator * union


def _techo(t, n):
    return -((-t.numerator * n) // t.denominator)


def _validar_parametros(ventana, fraccion, presupuesto=PRESUPUESTO_DEFECTO):
    if isinstance(ventana, bool) or not isinstance(ventana, int) or ventana < 1:
        raise ValueError(f"ventana debe ser un entero >= 1: {ventana!r}")
    if isinstance(fraccion, bool) or not isinstance(fraccion, (int, float)) or math.isnan(fraccion) \
            or not 0 < fraccion <= 1:
        raise ValueError(f"fraccion de boilerplate fuera de (0, 1]: {fraccion!r}")
    if isinstance(presupuesto, bool) or not isinstance(presupuesto, int) or presupuesto < 1:
        raise ValueError(f"presupuesto de muestreo debe ser un entero >= 1: {presupuesto!r}")


class Acumulador:
    """Shingles muestreados de un corpus que llega caso a caso (ver docstring del modulo). No guarda
    ningun texto: por caso, `array('Q')` ordenado de los hashes que pasan el limite vigente, la
    huella del conjunto COMPLETO (128 bits) y su tamaño."""

    def __init__(self, ventana=VENTANA_DEFECTO, presupuesto=PRESUPUESTO_DEFECTO):
        _validar_parametros(ventana, BOILERPLATE_DEFECTO, presupuesto)
        self.ventana, self.presupuesto = ventana, presupuesto
        self.ids, self.huellas, self.tamanos, self.arrays = [], [], [], []
        self._vistos = set()
        self.shingles_totales = 0
        self._guardados = 0

    def _limite(self):
        """Se conservan los hashes `h < limite`, con `h · suma < presupuesto · 2^64` (enteros exactos)."""
        if self.shingles_totales <= self.presupuesto:
            return 1 << 64
        return -(-(self.presupuesto << 64) // self.shingles_totales)

    def anadir(self, id_, family, texto):
        """Añade un caso: su texto se shinglea y se descarta aqui mismo (H4)."""
        if not (isinstance(id_, str) and isinstance(family, str) and isinstance(texto, str)):
            raise ValueError("cada documento es (id, family, texto), tres cadenas")
        if id_ in self._vistos:
            raise ValueError(f"id duplicado: {id_!r}")
        self._vistos.add(id_)
        b2, desde = hashlib.blake2b, int.from_bytes                      # `hash_shingle`, en linea (coste)
        completo = array("Q", sorted({desde(b2(sh.encode("utf-8"), digest_size=8).digest(), "little")
                                      for sh in shingles_de(texto, self.ventana)}))
        huella = hashlib.blake2b(completo.tobytes(), digest_size=16).digest()
        self.shingles_totales += len(completo)
        limite = self._limite()
        muestra = completo if not completo or completo[-1] < limite else completo[:bisect_left(completo, limite)]
        self.ids.append(id_)
        self.huellas.append(huella)
        self.tamanos.append(len(completo))
        self.arrays.append(muestra)
        self._guardados += len(muestra)
        if self._guardados > 2 * self.presupuesto:                      # poda amortizada
            self._podar()

    def _podar(self):
        limite = self._limite()
        total = 0
        for k, a in enumerate(self.arrays):
            if a and a[-1] >= limite:
                a = self.arrays[k] = a[:bisect_left(a, limite)]
            total += len(a)
        self._guardados = total

    def muestras(self):
        """`{id: array('Q')}` con el limite FINAL (el de la suma de todo el corpus)."""
        self._podar()
        return dict(zip(self.ids, self.arrays))

    def agrupar(self, umbral=UMBRAL_DEFECTO, fraccion_boilerplate=BOILERPLATE_DEFECTO):
        """Agrupa lo acumulado y CONSUME el acumulador (sus muestras se liberan al ordenarlas)."""
        t = _fraccion(umbral)
        _validar_parametros(self.ventana, fraccion_boilerplate, self.presupuesto)
        self._podar()
        return _agrupar_muestras(self, t, umbral, fraccion_boilerplate)


def _frecuencias(arrays):
    """Frecuencia documental EXACTA de la muestra: `(compartidos, solos)` = `{hash: df}` solo de los
    shingles con df >= 2 y cuantos tienen df == 1 (la mayoria, en un corpus real: no se guardan). Se
    cuenta por TRAMOS del espacio de hashes (`Counter` sobre el trozo de cada array ordenado que cae en
    el tramo): memoria O(tramo), no un dict de todo el corpus."""
    total = sum(len(a) for a in arrays if a)
    tramos = 1
    while tramos < 256 and total // tramos > 1 << 18:
        tramos *= 2
    paso = (1 << 64) // tramos
    compartidos, solos = {}, 0
    for b in range(tramos):
        lo, hi = b * paso, (b + 1) * paso if b < tramos - 1 else 1 << 64
        trozo = []
        for a in arrays:
            if a:
                trozo.extend(a[bisect_left(a, lo):bisect_left(a, hi)])
        for h, c in Counter(trozo).items():
            if c > 1:
                compartidos[h] = c
            else:
                solos += 1
    return compartidos, solos


def _boilerplate(compartidos, solos, n, fraccion):
    """H1: `(boiler, todo, n_boilerplate)`: los shingles con `df > fraccion · n` (estricto, con enteros)
    si `n >= N_MIN_BOILERPLATE`. `todo` si hasta un df == 1 lo supera (`fraccion < 1/n`)."""
    if n < N_MIN_BOILERPLATE:
        return set(), False, 0
    f = Fraction(repr(float(fraccion)))
    minimo = f.numerator * n // f.denominator + 1                        # menor df con df > fraccion · n
    if minimo <= 1:
        return set(compartidos), True, len(compartidos) + solos
    boiler = {h for h, c in compartidos.items() if c >= minimo}
    return boiler, False, len(boiler)


def _conjuntos(docs, ventana, fraccion, presupuesto=PRESUPUESTO_DEFECTO):
    """Para los tests (referencia de fuerza bruta): `(filtrados, originales, n_boilerplate)` en el orden
    de `docs`, como `frozenset` de hashes; `originales` sin muestrear."""
    acc = Acumulador(ventana, presupuesto)
    for d in docs:
        acc.anadir(*d)
    muestras = acc.muestras()
    boiler, todo, n_boiler = _boilerplate(*_frecuencias(list(muestras.values())), len(docs), fraccion)
    originales = [frozenset(hash_shingle(sh) for sh in shingles_de(d[2], ventana)) for d in docs]
    filtrados = [frozenset() if todo else frozenset(muestras[d[0]]) - boiler for d in docs]
    return filtrados, originales, n_boiler


def _agrupar_muestras(acc, t, umbral, fraccion):
    ids = acc.ids
    orden_id = sorted(range(len(ids)), key=lambda k: ids[k])
    n = len(ids)
    padre = list(range(n))

    def find(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    def unir(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            padre[max(ra, rb)] = min(ra, rb)

    # H3: colapso de duplicados EXACTOS por igualdad del conjunto ORIGINAL (huella + muestra)
    por_huella, reps, rep_de = {}, [], {}
    for k in orden_id:
        previos = por_huella.setdefault((acc.huellas[k], acc.tamanos[k]), [])
        for p in previos:
            if acc.arrays[p] == acc.arrays[k]:
                unir(p, k)
                rep_de[k] = p
                break
        else:
            previos.append(k)
            reps.append(k)
            rep_de[k] = k
    por_huella = None

    compartidos, solos = _frecuencias(acc.arrays)
    boiler, todo, n_boiler = _boilerplate(compartidos, solos, n, fraccion)
    df = compartidos.get
    mascara = (1 << 64) - 1
    avisos, ordenados, unicos = {}, {}, {}
    es_rep = set(reps)
    for k in range(n):
        if k not in es_rep:
            acc.arrays[k] = None                                         # duplicado exacto: ya unido
    for k in reps:
        a, acc.arrays[k] = acc.arrays[k], None                           # lo ordenado sustituye a la muestra
        f = [] if todo else [h for h in a if h not in boiler] if boiler else a
        if acc.tamanos[k] and not a:
            avisos[k] = AVISO_SIN_MUESTRAS
        elif a and len(f) * FRACCION_AVISO.denominator < FRACCION_AVISO.numerator * len(a):
            avisos[k] = AVISO_PLANTILLA.format(k=len(f), n=len(a))
        claves = sorted([(df(h, 1) << 64) | h for h in f])               # df ascendente, desempate por hash
        f = None
        ordenados[k] = array("Q", [c & mascara for c in claves])
        # un shingle con df == 1 solo esta en ESTE caso: nunca coincide con otro (no se indexa ni se sondea)
        unicos[k] = bisect_left(claves, 2 << 64)
        claves = None
    compartidos = df = None
    # los duplicados exactos heredan el aviso de su representante (mismo conjunto)
    lista_avisos = sorted(({"id": ids[k], "motivo": avisos[rep_de[k]]} for k in range(n) if rep_de[k] in avisos),
                          key=lambda a: a["id"])

    num, den = t.numerator, t.denominator
    indice = {}
    escaneos = verificados = 0
    for x in sorted(reps, key=lambda k: (len(ordenados[k]), ids[k])):
        ox = ordenados[x]
        lx = len(ox)
        if not lx:
            continue
        sondeo = lx - _techo(t, lx) + 1
        solapes, podados = {}, set()
        for i in range(unicos[x], sondeo):
            lista = indice.get(ox[i])
            if not lista:
                continue
            for y, j in lista:
                escaneos += 1
                if y in podados:
                    continue
                ly = len(ordenados[y])
                if ly * den < num * lx:                                  # longitud: |y| >= t·|x|
                    continue
                alfa = -((-num * (lx + ly)) // (num + den))               # ceil(t/(1+t)·(|x|+|y|))
                if solapes.get(y, 0) + 1 + min(lx - i - 1, ly - j - 1) >= alfa:
                    solapes[y] = solapes.get(y, 0) + 1
                else:                                                    # filtro posicional
                    solapes.pop(y, None)
                    podados.add(y)
        medio = lx + 1 - (-((-2 * num * lx) // (num + den)))              # mid-prefix PPJoin
        for i in range(unicos[x], medio):
            indice.setdefault(ox[i], []).append((x, i))
        if solapes:
            sx = set(ox)
            for y in sorted(solapes, key=lambda k: ids[k]):
                if find(x) == find(y):
                    continue
                verificados += 1
                inter = sum(1 for h in ordenados[y] if h in sx)
                if _supera(inter, lx + len(ordenados[y]) - inter, t):
                    unir(x, y)
    comp = defaultdict(list)
    for k in range(n):
        comp[find(k)].append(ids[k])
    grupos = sorted(sorted(g) for g in comp.values() if len(g) > 1)
    exacto = acc.shingles_totales <= acc.presupuesto
    return {"grupos": grupos, "casos": n, "boilerplate": n_boiler, "pares_verificados": verificados,
            "escaneos_indice": escaneos, "avisos": lista_avisos, "jaccard": "exacto" if exacto else "muestreado",
            "muestreo": {"r": 1.0 if exacto else acc.presupuesto / acc.shingles_totales,
                         "presupuesto": acc.presupuesto, "shingles": acc.shingles_totales},
            "parametros": {"umbral": umbral, "ventana": acc.ventana, "fraccion_boilerplate": fraccion,
                           "n_min_boilerplate": N_MIN_BOILERPLATE, "presupuesto": acc.presupuesto}}


def agrupar(documentos, umbral=UMBRAL_DEFECTO, ventana=VENTANA_DEFECTO, fraccion_boilerplate=BOILERPLATE_DEFECTO,
            presupuesto=PRESUPUESTO_DEFECTO):
    """Grupos de near-duplicates (ver docstring del modulo). Determinista ante el orden de entrada."""
    t = _fraccion(umbral)
    _validar_parametros(ventana, fraccion_boilerplate, presupuesto)
    acc = Acumulador(ventana, presupuesto)
    for d in documentos:
        if not (isinstance(d, (tuple, list)) and len(d) == 3):
            raise ValueError("cada documento es (id, family, texto), tres cadenas")
        acc.anadir(*d)
    acc._podar()
    return _agrupar_muestras(acc, t, umbral, fraccion_boilerplate)


# ------------------------------------------------------------------ CLI

class _Uso(Exception):
    pass


def _leer_documentos(ruta):
    docs = []
    try:
        with open(ruta, encoding="utf-8") as f:
            for n, linea in enumerate(f, 1):
                if not linea.strip():
                    continue
                try:
                    d = json.loads(linea)
                except (ValueError, RecursionError) as e:
                    raise _Uso(f"linea {n}: JSON ilegible ({type(e).__name__})") from None
                if not (isinstance(d, dict) and all(isinstance(d.get(k), str) for k in ("id", "family", "text"))):
                    raise _Uso(f"linea {n}: se espera {{\"id\", \"family\", \"text\"}} (tres cadenas)")
                docs.append((d["id"], d["family"], d["text"]))
    except OSError as e:
        raise _Uso(f"no se puede leer {ascii(ruta)}: {e.strerror or e}") from None
    except UnicodeDecodeError:
        raise _Uso(f"{ascii(ruta)}: no es UTF-8") from None
    return docs


def main(argv=None):
    ap = argparse.ArgumentParser(description="Near-duplicates deterministas por shingles/Jaccard (sin embeddings). "
                                             "Exit 0 ok, 2 uso o entrada ilegible.")
    ap.add_argument("documentos", help="JSONL: una linea {\"id\", \"family\", \"text\"} por caso")
    ap.add_argument("--umbral", type=float, default=UMBRAL_DEFECTO, help=f"Jaccard minimo, (0, 1] (default {UMBRAL_DEFECTO})")
    ap.add_argument("--ventana", type=int, default=VENTANA_DEFECTO, help=f"palabras por shingle (default {VENTANA_DEFECTO})")
    ap.add_argument("--boilerplate", type=float, default=BOILERPLATE_DEFECTO,
                    help=f"fraccion de casos por encima de la cual un shingle es texto fijo (default {BOILERPLATE_DEFECTO}; 1.0 = sin filtro)")
    ap.add_argument("--presupuesto", type=int, default=PRESUPUESTO_DEFECTO,
                    help=f"shingles muestreados en total; por debajo, Jaccard exacto (default {PRESUPUESTO_DEFECTO})")
    ap.add_argument("--json", action="store_true", help="salida JSON")
    args = ap.parse_args(argv)
    try:
        r = agrupar(_leer_documentos(args.documentos), args.umbral, args.ventana, args.boilerplate, args.presupuesto)
    except (_Uso, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, ensure_ascii=False, sort_keys=True))
        return 0
    for g in r["grupos"]:
        print("grupo: " + "  ".join(ascii(x) if not (x.isascii() and x.isprintable()) else x for x in g))
    for a in r["avisos"]:
        i = a["id"]
        print(f"aviso: {i if i.isascii() and i.isprintable() else ascii(i)}: {a['motivo']}", file=sys.stderr)
    print(f"{len(r['grupos'])} grupo(s) de near-duplicates en {r['casos']} caso(s); "
          f"{r['boilerplate']} shingle(s) de boilerplate ignorados; {r['pares_verificados']} par(es) verificados; "
          f"Jaccard {r['jaccard']}" + (f" (r = {r['muestreo']['r']:.4g})" if r["jaccard"] != "exacto" else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
