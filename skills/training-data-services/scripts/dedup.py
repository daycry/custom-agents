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

`agrupar(documentos, umbral, ventana, fraccion_boilerplate)` — `documentos`: iterable de
`(id, family, texto)` (ids unicos). Devuelve los GRUPOS de near-duplicates (componentes conexas del
grafo «Jaccard >= umbral»), deterministas: cada grupo ordenado por id y los grupos por su primer id.
  - Shingles: `ventana` palabras consecutivas (un texto mas corto que la ventana es UN shingle con
    todas sus palabras). Conjunto por caso; Jaccard = |A ∩ B| / |A ∪ B|, comparado con ENTEROS y el
    umbral como fraccion exacta (`Fraction(repr(umbral))`: 0.7 * 10 no es 7.000000000000001).
  - BOILERPLATE (texto fijo que se repetiria en todos los casos: prompt de sistema, plantillas): un
    shingle presente en MAS de `fraccion_boilerplate` de los casos (frecuencia documental) Y en al
    menos `MIN_FAMILIAS_BOILERPLATE` familias distintas se ignora. La condicion de familias evita el
    error contrario: 10 versiones casi iguales de UNA familia entre 12 casos tienen sus shingles en
    mas de la mitad de los casos, pero no son texto fijo. Con menos de `MIN_FAMILIAS_BOILERPLATE`
    familias en total no se filtra nada (limite declarado, conservador: mas grupos, nunca menos —
    un falso positivo excluye un caso; un falso negativo seria leakage). `fraccion_boilerplate=1.0`
    desactiva el filtro. Un caso cuyo contenido es TODO boilerplate solo se agrupa con los que
    tienen exactamente sus mismos shingles.
  - ESCALA (sin comparar todos los pares): indice invertido de shingles —como `duplicados` de
    code-health— recorrido con el FILTRO DE PREFIJO exacto de las uniones por similitud: con los
    shingles de cada caso ordenados por frecuencia ascendente (desempate por la propia cadena), dos
    casos con Jaccard >= t comparten al menos un shingle en sus prefijos de longitud
    `|A| - ceil(t·|A|) + 1`; solo esos pares se verifican, y no se verifica un par que ya esta en la
    misma componente. Filtro de longitud: `t·max <= min`. Coste ~ suma de (casos que comparten un
    shingle raro)², no n²; un grupo de 1 000 copias identicas se une con ~1 000 verificaciones.
  - `pares_verificados` en la salida hace visible el trabajo real (lo usan los tests de escala).

`texto_de_caso(caso)` — el texto variable de un caso (dict con `request`, `context`, `trajectory`):
objetos serializados con claves ordenadas (el orden de claves no cambia el texto).

Uso (exit 0 ok · 2 uso, fichero ausente o JSONL ilegible; nunca un traceback):
  dedup.py <documentos.jsonl> [--umbral 0.8] [--ventana 3] [--boilerplate 0.5] [--json]
  (una linea JSON por documento: {"id": "...", "family": "...", "text": "..."})
"""
import argparse
import json
import math
import os
import re
import sys
from collections import defaultdict
from fractions import Fraction

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

UMBRAL_DEFECTO = 0.8
VENTANA_DEFECTO = 3
BOILERPLATE_DEFECTO = 0.5
MIN_FAMILIAS_BOILERPLATE = 3
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


def _validar(documentos, ventana, fraccion):
    if isinstance(ventana, bool) or not isinstance(ventana, int) or ventana < 1:
        raise ValueError(f"ventana debe ser un entero >= 1: {ventana!r}")
    if isinstance(fraccion, bool) or not isinstance(fraccion, (int, float)) or math.isnan(fraccion) \
            or not 0 < fraccion <= 1:
        raise ValueError(f"fraccion de boilerplate fuera de (0, 1]: {fraccion!r}")
    docs, vistos = [], set()
    for d in documentos:
        if not (isinstance(d, (tuple, list)) and len(d) == 3 and all(isinstance(x, str) for x in d)):
            raise ValueError("cada documento es (id, family, texto), tres cadenas")
        if d[0] in vistos:
            raise ValueError(f"id duplicado: {d[0]!r}")
        vistos.add(d[0])
        docs.append(tuple(d))
    return docs


def _conjuntos(docs, ventana, fraccion):
    """`(filtrados, originales_de_vacios, n_boilerplate, df, nombres)` en el orden de `docs`: cada
    conjunto es de ids enteros de shingle (`nombres[i]` es la cadena del id `i`). `originales_de_vacios`
    guarda el conjunto original SOLO de los casos que se quedan vacios al quitar el boilerplate."""
    ids, nombres, originales = {}, [], []
    for _id, _fam, texto in docs:
        s = set()
        for sh in shingles_de(texto, ventana):
            k = ids.get(sh)
            if k is None:
                k = ids[sh] = len(nombres)
                nombres.append(sh)
            s.add(k)
        originales.append(s)
    df = [0] * len(nombres)
    for s in originales:
        for k in s:
            df[k] += 1
    n = len(docs)
    boiler = set()
    if len({fam for _i, fam, _t in docs}) >= MIN_FAMILIAS_BOILERPLATE:
        frecuentes = {k for k, c in enumerate(df) if c > fraccion * n}
        familias = defaultdict(set)
        if frecuentes:
            for (_i, fam, _t), s in zip(docs, originales):
                for k in s & frecuentes:
                    familias[k].add(fam)
        boiler = {k for k in frecuentes if len(familias[k]) >= MIN_FAMILIAS_BOILERPLATE}
    filtrados, vacios = [], {}
    for i, s in enumerate(originales):
        f = frozenset(s - boiler) if boiler else frozenset(s)
        filtrados.append(f)
        if not f:
            vacios[i] = frozenset(s)
    return filtrados, vacios, len(boiler), df, nombres


def agrupar(documentos, umbral=UMBRAL_DEFECTO, ventana=VENTANA_DEFECTO, fraccion_boilerplate=BOILERPLATE_DEFECTO):
    """Grupos de near-duplicates (ver docstring del modulo). Determinista ante el orden de entrada."""
    t = _fraccion(umbral)
    docs = sorted(_validar(documentos, ventana, fraccion_boilerplate), key=lambda d: d[0])
    conj, vacios, n_boiler, df, nombres = _conjuntos(docs, ventana, fraccion_boilerplate)
    padre = list(range(len(docs)))

    def find(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    def unir(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            padre[max(ra, rb)] = min(ra, rb)

    usados = sorted({k for s in conj for k in s}, key=lambda k: (df[k], nombres[k]))
    rango = {k: r for r, k in enumerate(usados)}
    ordenados, prefijos = [], []
    indice = defaultdict(list)
    for i, s in enumerate(conj):
        orden = sorted(rango[k] for k in s)
        p = len(orden) - _techo(t, len(orden)) + 1 if orden else 0
        ordenados.append(orden)
        prefijos.append(orden[:p])
        for r in orden[:p]:
            indice[r].append(i)
    verificados = 0
    for i, s in enumerate(conj):
        if not s:
            continue
        candidatos = set()
        for r in prefijos[i]:
            candidatos.update(indice[r])
        li = len(s)
        for j in sorted(candidatos):
            if j <= i or find(i) == find(j):
                continue
            lj = len(conj[j])
            if min(li, lj) * t.denominator < t.numerator * max(li, lj):
                continue                                         # filtro de longitud: J <= min/max
            verificados += 1
            inter = len(s & conj[j])
            if _supera(inter, li + lj - inter, t):
                unir(i, j)
    por_original = {}
    for i, orig in sorted(vacios.items()):
        if orig in por_original:
            unir(por_original[orig], i)
        else:
            por_original[orig] = i
    comp = defaultdict(list)
    for i, d in enumerate(docs):
        comp[find(i)].append(d[0])
    grupos = sorted(sorted(g) for g in comp.values() if len(g) > 1)
    return {"grupos": grupos, "casos": len(docs), "boilerplate": n_boiler, "pares_verificados": verificados,
            "parametros": {"umbral": umbral, "ventana": ventana, "fraccion_boilerplate": fraccion_boilerplate,
                           "min_familias_boilerplate": MIN_FAMILIAS_BOILERPLATE}}


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
    ap.add_argument("--json", action="store_true", help="salida JSON")
    args = ap.parse_args(argv)
    try:
        r = agrupar(_leer_documentos(args.documentos), args.umbral, args.ventana, args.boilerplate)
    except (_Uso, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(r, ensure_ascii=False, sort_keys=True))
        return 0
    for g in r["grupos"]:
        print("grupo: " + "  ".join(ascii(x) if not (x.isascii() and x.isprintable()) else x for x in g))
    print(f"{len(r['grupos'])} grupo(s) de near-duplicates en {r['casos']} caso(s); "
          f"{r['boilerplate']} shingle(s) de boilerplate ignorados; {r['pares_verificados']} par(es) verificados")
    return 0


if __name__ == "__main__":
    sys.exit(main())
