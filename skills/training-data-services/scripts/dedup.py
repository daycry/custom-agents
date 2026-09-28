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

`agrupar(documentos, umbral, ventana, fraccion_boilerplate, presupuesto, benchmark_ids)` — `documentos`: iterable de
`(id, family, texto)` (ids unicos; puede ser un generador: cada texto se descarta al shinglearlo).
Devuelve los GRUPOS de near-duplicates (componentes conexas del grafo «Jaccard >= umbral»),
deterministas: cada grupo ordenado por id y los grupos por su primer id. `Acumulador` es la misma
maquina en streaming (`anadir(id, family, texto)` y despues `agrupar(umbral, fraccion, benchmark_ids)`):
el ensamblador la alimenta caso a caso sin guardar ningun texto (fix1, H4/H5).
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
    muestreados»; entonces solo se agrupa con un duplicado EXACTO). Con `r < 1` el Jaccard es exacto
    respecto a la MUESTRA, no al real (#145): error tipico `±z·sqrt(J(1-J)/k)`, k = shingles muestreados
    de la union del par (1 000 shingles por caso y r = 0.1: k ~ 110, ±0.076 con z = 2).
  - CRUCE CONSERVADOR (#145, solo con `r < 1` y `benchmark_ids`): un par que CRUZA train/benchmark
    con Jaccard muestreado `>= umbral - min(z·sqrt(u(1-u)/k), 0.2, umbral/2)` sale en `cruces`
    (`[[id de train, id de benchmark]]`, con todas las copias exactas de train); lo usa el ensamblador
    solo para la exclusion anti-leakage; los `grupos` siguen con el umbral. `cruce` lo declara
    (`criterio`, `z`, `margen_max`, `umbral_minimo`). Con `r = 1` no hace falta (`criterio: umbral`).
  - MEMORIA (#142): un `array('Q')` por caso (8 B por shingle muestreado) y, al agrupar, su frecuencia
    documental EXACTA como un `array('I')` alineado (4 B), sin ningun dict de todo el corpus: se cuenta
    por TRAMOS del espacio de hashes (#144: 1 tramo si caben `CONTEO_MAX_TRAMO` = 2^21 shingles; mas,
    potencia de 2, solo si no), con UN `Counter` por tramo que se libera al acabarlo (~190 MiB como
    mucho). Los shingles con df == 1 nunca coinciden con otro caso: ni se indexan ni se sondean. Cota
    declarada con `presupuesto = 10^7` y casi todo con df >= 2 (pares casi iguales): <= ~0.9 GiB.
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
    tiene que poder llegar al solapamiento minimo `ceil(t/(1+t)·(|x|+|y|))`). Exacto sobre los conjuntos
    comparados (la muestra, con `r < 1`): ningun par con Jaccard >= t se pierde. CUBOS (#141): el
    indice agrupa los postings de un shingle por COMPONENTE; un cubo cuya componente ya es la de x se
    salta entero en O(1) y uno grande (> `CUBO_VERIFICACION` postings) se verifica por UN miembro antes
    de recorrerlo: dentro de un grupo de m near-duplicates, O(m·|x|) (antes O(m^2·|x|): se escaneaba el
    mid-prefix aunque x e y ya estuvieran en el mismo grupo). Peor caso real declarado: m casos que
    comparten muchos shingles de prefijo SIN llegar al umbral (cada uno su componente), O(m^2·|x|)
    escaneos, el de PPJoin; el texto comun que no llega a boilerplate (#115b) queda al final del
    orden y no entra en el mid-prefix de nadie: 0 escaneos.
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
CONTEO_MAX_TRAMO = 1 << 21         # #144: shingles contados por tramo (un `Counter` transitorio de <= ~190 MiB)
CUBO_VERIFICACION = 8              # #141: un cubo del indice con mas postings se verifica por UN miembro antes
Z_CRUCE = 2.0                      # #145: margen z*sqrt(J(1-J)/k) del cruce train/benchmark con r < 1
MARGEN_MAX_CRUCE = Fraction(1, 5)  # #145: tope del margen (el umbral del cruce nunca baja de umbral - 0.2)
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

    def agrupar(self, umbral=UMBRAL_DEFECTO, fraccion_boilerplate=BOILERPLATE_DEFECTO, benchmark_ids=None):
        """Agrupa lo acumulado y CONSUME el acumulador (sus muestras se liberan al ordenarlas).
        `benchmark_ids`: ids del lado de benchmark (#145: con `r < 1`, `cruces` conservadores)."""
        t = _fraccion(umbral)
        _validar_parametros(self.ventana, fraccion_boilerplate, self.presupuesto)
        self._podar()
        return _agrupar_muestras(self, t, umbral, fraccion_boilerplate, benchmark_ids)


def _tramos(total):
    """#144: tramos ADAPTATIVOS del conteo: 1 si los `total` shingles muestreados caben en el
    presupuesto de conteo (`CONTEO_MAX_TRAMO`); si no, la menor potencia de 2 (<= 256) que lo cumple."""
    tramos = 1
    while tramos < 256 and total > tramos * CONTEO_MAX_TRAMO:
        tramos *= 2
    return tramos


def _frecuencias(arrays):
    """Frecuencia documental EXACTA de la muestra, SIN un dict de todo el corpus (#142): `(dfs, hist)`
    con `dfs[k]` un `array('I')` alineado con `arrays[k]` (la df de cada uno de sus hashes; vacio si
    `arrays[k]` es None o vacio) e `hist` = `Counter` {df: cuantos shingles DISTINTOS la tienen} (lo
    que necesita el boilerplate). Se cuenta por TRAMOS del espacio de hashes (`_tramos`, #144): en cada
    uno, UN `Counter` sobre la concatenacion de los trozos de cada array ordenado que caen en el (cursor
    por array: cada elemento se visita una vez) y la df se copia a `dfs`; el `Counter` se libera al
    acabar el tramo. Coste: O(tramos · n + total) (el termino O(tramos · n) ya solo con > 2^21 shingles)."""
    vivos = [(k, a) for k, a in enumerate(arrays) if a]
    tramos = _tramos(sum(len(a) for _k, a in vivos))
    paso = (1 << 64) // tramos
    dfs = [array("I") for _ in arrays]
    pos = [0] * len(vivos)
    hist = Counter()
    for b in range(tramos):
        ultimo = b == tramos - 1
        hi = (b + 1) * paso
        trozo, cortes = array("Q"), []
        for i, (k, a) in enumerate(vivos):
            j = pos[i]
            e = len(a) if ultimo else bisect_left(a, hi, j)
            if e > j:
                trozo.extend(a[j:e])
                cortes.append((k, e - j))
                pos[i] = e
        cuenta = Counter(trozo)                                          # UN conteo por tramo (C)
        hist.update(cuenta.values())
        vals = array("I", map(cuenta.__getitem__, trozo))                # df de cada elemento, en su orden
        cuenta = trozo = None
        o = 0
        for k, n in cortes:
            dfs[k].extend(vals[o:o + n])
            o += n
        vals = cortes = None
    return dfs, hist


def _boilerplate(hist, n, fraccion):
    """H1: `(minimo, todo, n_boilerplate)`: un shingle es plantilla si `df >= minimo` (el menor df con
    `df > fraccion · n`, estricto, con enteros) y solo si `n >= N_MIN_BOILERPLATE` (si no, `minimo`
    None: nada es plantilla). `todo` si hasta un df == 1 lo supera (`fraccion < 1/n`)."""
    if n < N_MIN_BOILERPLATE:
        return None, False, 0
    f = Fraction(repr(float(fraccion)))
    minimo = f.numerator * n // f.denominator + 1                        # menor df con df > fraccion · n
    if minimo <= 1:
        return minimo, True, sum(hist.values())
    return minimo, False, sum(c for d, c in hist.items() if d >= minimo)


def _conjuntos(docs, ventana, fraccion, presupuesto=PRESUPUESTO_DEFECTO):
    """Para los tests (referencia de fuerza bruta): `(filtrados, originales, n_boilerplate)` en el orden
    de `docs`, como `frozenset` de hashes; `originales` sin muestrear."""
    acc = Acumulador(ventana, presupuesto)
    for d in docs:
        acc.anadir(*d)
    muestras = acc.muestras()
    dfs, hist = _frecuencias(list(muestras.values()))
    minimo, todo, n_boiler = _boilerplate(hist, len(docs), fraccion)
    df_de = dict(zip(muestras, dfs))
    originales = [frozenset(hash_shingle(sh) for sh in shingles_de(d[2], ventana)) for d in docs]
    filtrados = [frozenset() if todo else frozenset(h for h, c in zip(muestras[d[0]], df_de[d[0]])
                                                    if minimo is None or c < minimo) for d in docs]
    return filtrados, originales, n_boiler


def _filtro_posicional(num, den, lx, ly, i, j, previo):
    """PPJoin: lo que queda de ambos detras de la coincidencia (posiciones `i` de x y `j` de y) puede
    llegar al solapamiento minimo `ceil(t/(1+t)·(|x|+|y|))` con `previo` coincidencias ya contadas."""
    alfa = -((-num * (lx + ly)) // (num + den))
    return previo + 1 + min(lx - i - 1, ly - j - 1) >= alfa


def _umbral_cruce(umbral):
    """#145: umbral MINIMO del cruce conservador: `umbral - min(MARGEN_MAX_CRUCE, umbral/2)` (exacto)."""
    t = _fraccion(umbral)
    return t - min(MARGEN_MAX_CRUCE, t / 2)


def _margen_cruce(u, union):
    """#145: margen de la estimacion muestreada del Jaccard de un par con `union` shingles muestreados
    en su union: `z·sqrt(u(1-u)/k)` (error tipico de una proporcion con k muestras), acotado a
    `min(MARGEN_MAX_CRUCE, u/2)`."""
    tope = min(float(MARGEN_MAX_CRUCE), u / 2)
    return min(Z_CRUCE * math.sqrt(u * (1 - u) / union), tope) if union else tope


def _cruces_conservadores(reps, ordenados, unicos, ids, clases, es_bench, umbral):
    """#145 (b), solo con `r < 1`: pares que CRUZAN train/benchmark con Jaccard muestreado
    `>= umbral - margen` (`_margen_cruce`). Otra pasada PPJoin con el umbral minimo (`_umbral_cruce`)
    en la que cada lado solo sondea el indice del otro; un representante de train ya marcado no se
    vuelve a buscar. Devuelve `[[id train, id benchmark]]` con TODOS los miembros de train de la clase
    de duplicados exactos del representante."""
    u = float(umbral)
    tl = _umbral_cruce(umbral)
    num, den = tl.numerator, tl.denominator
    lados = {k: (any(not es_bench(ids[m]) for m in clases[k]), any(es_bench(ids[m]) for m in clases[k]))
             for k in reps}
    indices = ({}, {})                                                   # 0: clases con train; 1: con benchmark
    marcado = {}                                                         # rep de train -> rep de benchmark
    for x in sorted(reps, key=lambda k: (len(ordenados[k]), ids[k])):
        ox = ordenados[x]
        lx = len(ox)
        if not lx:
            continue
        sondeo = lx - _techo(tl, lx) + 1
        for lado in (0, 1):
            if not lados[x][lado] or (lado == 0 and x in marcado):
                continue
            solapes, podados = {}, set()
            opuesto = indices[1 - lado]
            for i in range(unicos[x], sondeo):
                for y, j in opuesto.get(ox[i], ()):
                    if y in podados or (lado == 1 and y in marcado):
                        continue
                    ly = len(ordenados[y])
                    if ly * den < num * lx:
                        continue
                    if _filtro_posicional(num, den, lx, ly, i, j, solapes.get(y, 0)):
                        solapes[y] = solapes.get(y, 0) + 1
                    else:
                        solapes.pop(y, None)
                        podados.add(y)
            if not solapes:
                continue
            sx = set(ox)
            for y in sorted(solapes, key=lambda k: ids[k]):
                if lado == 1 and y in marcado:
                    continue
                inter = sum(1 for h in ordenados[y] if h in sx)
                union = lx + len(ordenados[y]) - inter
                if _supera(inter, union, tl) and inter / union >= u - _margen_cruce(u, union):
                    tr, be = (x, y) if lado == 0 else (y, x)
                    marcado[tr] = be
                    if lado == 0:
                        break
        medio = lx + 1 - (-((-2 * num * lx) // (num + den)))
        for lado in (0, 1):
            if lados[x][lado]:
                for i in range(unicos[x], medio):
                    indices[lado].setdefault(ox[i], []).append((x, i))
    pares = []
    for tr, be in marcado.items():
        bench = min(ids[m] for m in clases[be] if es_bench(ids[m]))
        pares += [[ids[m], bench] for m in clases[tr] if not es_bench(ids[m])]
    return sorted(pares)


def _agrupar_muestras(acc, t, umbral, fraccion, benchmark_ids=None):
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

    dfs, hist = _frecuencias(acc.arrays)                                 # #142: df por elemento, sin dict global
    minimo, todo, n_boiler = _boilerplate(hist, n, fraccion)
    hist = None
    mascara = (1 << 64) - 1
    avisos, ordenados, unicos = {}, {}, {}
    es_rep = set(reps)
    for k in range(n):
        if k not in es_rep:
            acc.arrays[k] = dfs[k] = None                                # duplicado exacto: ya unido
    for k in reps:
        a, acc.arrays[k] = acc.arrays[k], None                           # lo ordenado sustituye a la muestra
        d, dfs[k] = dfs[k], None
        if todo:
            claves = []
        elif minimo is None:
            claves = sorted([(c << 64) | h for h, c in zip(a, d)])       # df ascendente, desempate por hash
        else:
            claves = sorted([(c << 64) | h for h, c in zip(a, d) if c < minimo])
        if acc.tamanos[k] and not a:
            avisos[k] = AVISO_SIN_MUESTRAS
        elif a and len(claves) * FRACCION_AVISO.denominator < FRACCION_AVISO.numerator * len(a):
            avisos[k] = AVISO_PLANTILLA.format(k=len(claves), n=len(a))
        ordenados[k] = array("Q", [c & mascara for c in claves])
        # un shingle con df == 1 solo esta en ESTE caso: nunca coincide con otro (no se indexa ni se sondea)
        unicos[k] = bisect_left(claves, 2 << 64)
        a = d = claves = None
    dfs = None
    # los duplicados exactos heredan el aviso de su representante (mismo conjunto)
    lista_avisos = sorted(({"id": ids[k], "motivo": avisos[rep_de[k]]} for k in range(n) if rep_de[k] in avisos),
                          key=lambda a: a["id"])

    num, den = t.numerator, t.denominator
    # #141: indice de CUBOS. Un cubo es un `array('q')` `[raiz, y1, j1, y2, j2, ...]` con postings de UNA
    # componente (las componentes solo se unen: la invariante se mantiene); `indice[h]` es el cubo si
    # solo hay uno (lo normal) o una lista de cubos. Un cubo cuya raiz ya es la de x se salta entero en
    # O(1); uno grande (> CUBO_VERIFICACION postings) se verifica por UN miembro antes de recorrerlo
    indice = {}
    escaneos = verificados = 0
    for x in sorted(reps, key=lambda k: (len(ordenados[k]), ids[k])):
        ox = ordenados[x]
        lx = len(ox)
        if not lx:
            continue
        sondeo = lx - _techo(t, lx) + 1
        solapes, podados, probados = {}, set(), set()
        sx = None
        for i in range(unicos[x], sondeo):
            v = indice.get(ox[i])
            if v is None:
                continue
            for cubo in ((v,) if type(v) is array else v):
                raiz = cubo[0] = find(cubo[0])
                if raiz == find(x):
                    continue
                if len(cubo) > 2 * CUBO_VERIFICACION + 1 and raiz not in probados:
                    probados.add(raiz)
                    y = cubo[1]
                    ly = len(ordenados[y])
                    if ly * den >= num * lx:
                        sx = set(ox) if sx is None else sx
                        verificados += 1
                        podados.add(y)                                   # ya verificado: no se cuenta otra vez
                        inter = sum(1 for h in ordenados[y] if h in sx)
                        if _supera(inter, lx + ly - inter, t):
                            unir(x, y)
                            continue
                for k in range(1, len(cubo), 2):
                    y, j = cubo[k], cubo[k + 1]
                    escaneos += 1
                    if y in podados:
                        continue
                    ly = len(ordenados[y])
                    if ly * den < num * lx:                              # longitud: |y| >= t·|x|
                        continue
                    if _filtro_posicional(num, den, lx, ly, i, j, solapes.get(y, 0)):
                        solapes[y] = solapes.get(y, 0) + 1
                    else:                                                # filtro posicional
                        solapes.pop(y, None)
                        podados.add(y)
        if solapes:
            sx = set(ox) if sx is None else sx
            for y in sorted(solapes, key=lambda k: ids[k]):
                if find(x) == find(y):
                    continue
                verificados += 1
                inter = sum(1 for h in ordenados[y] if h in sx)
                if _supera(inter, lx + len(ordenados[y]) - inter, t):
                    unir(x, y)
        sx = None
        rx = find(x)
        medio = lx + 1 - (-((-2 * num * lx) // (num + den)))              # mid-prefix PPJoin
        for i in range(unicos[x], medio):
            h = ox[i]
            v = indice.get(h)
            if v is None:
                indice[h] = array("q", (rx, x, i))
                continue
            ultimo = v if type(v) is array else v[-1]
            if find(ultimo[0]) == rx:
                ultimo[0] = rx
                ultimo.extend((x, i))
            elif type(v) is array:
                indice[h] = [v, array("q", (rx, x, i))]
            else:
                v.append(array("q", (rx, x, i)))
    indice = None
    exacto = acc.shingles_totales <= acc.presupuesto
    cruces = []
    if benchmark_ids is not None and not exacto:
        clases = defaultdict(list)
        for k in range(n):
            clases[rep_de[k]].append(k)
        bench = set(benchmark_ids)
        cruces = _cruces_conservadores(reps, ordenados, unicos, ids, clases, bench.__contains__, umbral)
    comp = defaultdict(list)
    for k in range(n):
        comp[find(k)].append(ids[k])
    grupos = sorted(sorted(g) for g in comp.values() if len(g) > 1)
    if exacto or benchmark_ids is None:
        cruce = {"criterio": "umbral"}
    else:
        cruce = {"criterio": "conservador", "z": Z_CRUCE, "margen_max": float(MARGEN_MAX_CRUCE),
                 "umbral_minimo": float(_umbral_cruce(umbral)),
                 "margen": "z*sqrt(J(1-J)/k), k = shingles muestreados de la union del par"}
    return {"grupos": grupos, "casos": n, "boilerplate": n_boiler, "pares_verificados": verificados,
            "escaneos_indice": escaneos, "avisos": lista_avisos, "jaccard": "exacto" if exacto else "muestreado",
            "muestreo": {"r": 1.0 if exacto else acc.presupuesto / acc.shingles_totales,
                         "presupuesto": acc.presupuesto, "shingles": acc.shingles_totales},
            "cruce": cruce, "cruces": cruces,
            "parametros": {"umbral": umbral, "ventana": acc.ventana, "fraccion_boilerplate": fraccion,
                           "n_min_boilerplate": N_MIN_BOILERPLATE, "presupuesto": acc.presupuesto}}


def agrupar(documentos, umbral=UMBRAL_DEFECTO, ventana=VENTANA_DEFECTO, fraccion_boilerplate=BOILERPLATE_DEFECTO,
            presupuesto=PRESUPUESTO_DEFECTO, benchmark_ids=None):
    """Grupos de near-duplicates (ver docstring del modulo). Determinista ante el orden de entrada."""
    t = _fraccion(umbral)
    _validar_parametros(ventana, fraccion_boilerplate, presupuesto)
    acc = Acumulador(ventana, presupuesto)
    for d in documentos:
        if not (isinstance(d, (tuple, list)) and len(d) == 3):
            raise ValueError("cada documento es (id, family, texto), tres cadenas")
        acc.anadir(*d)
    acc._podar()
    return _agrupar_muestras(acc, t, umbral, fraccion_boilerplate, benchmark_ids)


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
