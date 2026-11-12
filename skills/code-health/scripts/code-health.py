#!/usr/bin/env python3
"""
code-health.py — informe DETERMINISTA y agnóstico de lenguaje de la salud de un árbol de código
(skill `code-health`, iniciativa memory-health). Cuatro medidas, todas aproximadas y explicadas:

  1. Duplicados     — shingles de `--window` líneas de código normalizadas (identificadores → `id`,
                      números/cadenas → `num`/`str`, comentarios y líneas vacías fuera) entre
                      ficheros DISTINTOS; pares `fichero:línea ↔ fichero:línea` y % de líneas
                      cubiertas por algún duplicado. Cada par cuenta un bloque contiguo (se
                      colapsan las ventanas solapadas).
  2. Tamaño/complejidad — por fichero: líneas de código, profundidad máxima de anidamiento
                      (llaves `{}` o indentación, según el lenguaje) y FUNCIONES LARGAS
                      (cabecera detectada por regex por lenguaje, cuerpo hasta la siguiente cabecera
                      del mismo nivel o menor) con más de `--min-lines` × 5 líneas. Heurística: no
                      es un parser; sirve para ordenar, no para juzgar una función concreta.
  3. Hotspots       — ficheros más cambiados en `git log --since <N> days --name-only`, cruzados con
                      su tamaño: puntuación `cambios × log2(líneas+1)` (los grandes Y que cambian).
  4. TODO/FIXME/HACK/XXX — marcadores con su antigüedad en días (`git blame -L` por línea; sin git,
                      solo el recuento).

Sin git (o fuera de un repo) se omiten 3 y la antigüedad de 4, con AVISO dentro del informe.
Con git, los ficheros VERSIONADOS bajo directorios de terceros o de build que el recorrido excluye
(`vendor/`, `node_modules/`, `dist/`, `build/`, `target/`…) se CUENTAN por directorio y se avisan,
sin analizarlos (`excluidos_versionados` en el JSON; null sin git).

Uso:
  code-health.py <ruta> [--json] [--min-lines 6] [--langs py,js,ts,…] [--window 8]
                        [--exclude-tests] [--exclude-path PREFIJO ...] [--since 90]
                        [--baseline informe.json] [--top 10] [--max-files N] [--max-seconds S]
                        [--max-occ N] [--max-pairs N] [--max-bytes N]
Exit: 0 siempre (informe emitido) · 2 error de uso (ruta inexistente, baseline ilegible).

`--exclude-path` (repetible, aditivo, default sin exclusiones): prefijo relativo a la raíz (p.ej.
`interop`, `interop/opencode`) para sacar del informe carpetas GENERADAS (como `interop/`, salida de
`export-interop.py`) que duplican por construcción el fichero del que se generaron.
"""
import argparse
import time
import datetime as _dt
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

LANGS_DEFAULT = "py,js,ts,tsx,jsx,php,go,java,rb,cs,kt,rs"
EXCLUDE_DIRS = {"vendor", "node_modules", "dist", "build", ".git", "__pycache__", ".venv", "venv",
                "target", ".next", "coverage", ".idea", ".vscode", "worktrees", "site-packages"}
# Toda carpeta oculta (`.pytest_cache`, `.mypy_cache`, `.tox`, `.ruff_cache`…) es salida de herramientas o
# de editor, no código del proyecto: se salta SIEMPRE (T-07, plugin-audit-2; en este repo `.pytest_cache`
# eran 7.204 de 7.644 ficheros y el informe no terminaba).
# Topes por defecto de la CLI (0 = sin tope): ficheros y segundos de la parte de análisis. Si se
# alcanzan, el informe es PARCIAL y lo dice (`parcial: true` + aviso); nunca se completa con datos inventados.
MAX_FICHEROS_DEFAULT = 3000
MAX_SEGUNDOS_DEFAULT = 100
# Ocurrencias que se emparejan por ventana de líneas: el emparejado es cuadrático por ventana, y con
# ficheros casi idénticos (copias generadas, plantillas) una sola ventana aparece miles de veces (120
# ficheros iguales agotaban 1 GiB). Por encima del tope solo se emparejan las primeras (orden de ruta):
# memoria acotada y el informe se declara PARCIAL (el % duplicado es entonces un mínimo).
MAX_OCURRENCIAS_DEFAULT = 50
# Tope TOTAL de pares de líneas duplicadas que se retienen (T-07 fix1, gap 6): con el tope por ventana la
# memoria seguía siendo Σ min(ocurrencias, 50)² pares (60 copias de una plantilla de 500 líneas = 604 K pares,
# 75 MiB). Cada par es un entero en un `set`; al llegar al tope se deja de emparejar y el informe es PARCIAL.
MAX_PARES_DEFAULT = 100000
# Un fichero de código por encima de este tamaño (bundles minificados, volcados, generados) se omite con aviso:
# leerlo y normalizarlo no se interrumpía (T-07 fix1, gap 17). 0 = sin tope.
MAX_BYTES_DEFAULT = 2000000


class PlazoAgotado(Exception):
    """El plazo del análisis (`--max-seconds`) se agotó en mitad de una lectura o de una normalización."""
# Subconjunto de EXCLUDE_DIRS que es código de terceros o salida de build: si git los versiona,
# el informe lo avisa (sin analizarlos). Fuera quedan .git y las carpetas de editor.
VENDOR_BUILD_DIRS = {"vendor", "node_modules", "dist", "build", "target", ".next", "coverage",
                     ".venv", "venv", "__pycache__"}
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec|specs)(/|$)|(^|/)test_[^/]+\.py$|[._-](test|spec)\.[a-z]+$")
# Marcador = la palabra seguida (con o sin espacio) de `:`/`-`/`—`, o PEGADA (sin espacio) a `(`
# (estilo `TODO(alice):`); o al COMIENZO de un comentario («# TODO revisar»), en cuyo caso solo
# cuenta si la palabra siguiente NO es un artículo/preposición/pronombre castellano (ver
# PROSA_ES_TRAS_MARCADOR más abajo) — evita el falso positivo «# TODO el histórico como ventana»
# (prosa) sin dejar de detectar «# TODO revisar esto» (anotación real). Un `(` con ESPACIO antes
# («TODO (ADRs, arquitectura,») sigue sin ser un separador válido (T-01 original): es prosa
# castellana, no una anotación de código. Revisión R1 (A-1/B-9): antes «TODO» al comienzo de
# comentario contaba siempre, sin mirar la palabra siguiente.
#
# LÍMITE CONOCIDO (revisión R2, R2-3): un marcador REAL en castellano que NO lleve `:`/`-`/`—`
# ni vaya PEGADO a `(` justo tras la palabra («# TODO en producción esto falla», «# FIXME la
# caché») se excluye igual que la prosa, porque la palabra siguiente («en», «la») no está en
# `PROSA_ES_TRAS_MARCADOR` por casualidad de vocabulario, sino porque no hay forma barata de
# distinguir «marcador + frase en castellano» de «prosa que empieza por esa palabra» sin un
# parser. Es un compromiso deliberado, no un bug: la convención esperada es `TODO:` con dos
# puntos (o `TODO(autor):`), y así se documenta también en `skills/code-health/SKILL.md`.
PROSA_ES_TRAS_MARCADOR = {
    "el", "la", "los", "las", "lo", "un", "una", "unos", "unas",
    "de", "del", "al", "que", "para", "con", "en", "y", "o", "u", "e",
    "su", "sus", "este", "esta", "estos", "estas", "ese", "esa", "esos", "esas",
}
_MARCADOR_SEP_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b(?=\s*[:\-—]|\s*$)")
_MARCADOR_PEGADO_PAREN_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\(")
_MARCADOR_INICIO_RE = re.compile(r"(?:^|(?<=[#/*!]))\s*(TODO|FIXME|HACK|XXX)\b(.*)$")
_PALABRA_RE = re.compile(r"[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+")


def _tipo_marcador(raw):
    """Devuelve TODO/FIXME/HACK/XXX si `raw` es una anotación real, o None si no lo es
    (prosa castellana al comienzo de un comentario)."""
    m = _MARCADOR_SEP_RE.search(raw)
    if m:
        return m.group(1)
    m = _MARCADOR_PEGADO_PAREN_RE.search(raw)
    if m:
        return m.group(1)
    m = _MARCADOR_INICIO_RE.search(raw)
    if not m:
        return None
    resto = m.group(2).strip()
    if not resto:
        return m.group(1)
    if resto.startswith("("):
        return None   # `(` con espacio antes = prosa, no separador (ver comentario arriba)
    palabra = _PALABRA_RE.match(resto)
    if palabra and palabra.group(0).lower() in PROSA_ES_TRAS_MARCADOR:
        return None
    return m.group(1)


# Líneas de DOCUMENTACIÓN que enumeran marcadores CITADOS entre backticks como ejemplos (p. ej.
# `journal.py:41`: «`más tarde`, `TODO:`, `remind me`…») no son anotaciones reales: el propio
# marcador aparece entrecomillado, como un ítem más de una lista de ≥ 2 spans entre backticks.
# Una anotación real nunca lleva el `TODO:`/`FIXME:` entre backticks: si hay backticks, citan
# OTRA cosa (ficheros, identificadores) — «TODO: unificar `a.py`, `b.py`» SÍ cuenta (revisión R1,
# B-2: la regla vieja excluía cualquier línea con 2 backtick-spans separados por coma sin mirar
# si el marcador estaba dentro de uno, y así suprimía anotaciones reales como esa).
_MARCADOR_ENTRE_BACKTICKS_RE = re.compile(r"`\s*(TODO|FIXME|HACK|XXX)\b[^`\n]*`")
_BACKTICK_SPAN_RE = re.compile(r"`[^`\n]*`")


def _es_enumeracion_de_marcadores(raw):
    """True si la línea enumera marcadores ENTRE BACKTICKS (documentación de patrones léxicos),
    no una anotación real."""
    if not _MARCADOR_ENTRE_BACKTICKS_RE.search(raw):
        return False
    return len(_BACKTICK_SPAN_RE.findall(raw)) >= 2


# Revisión R2 (R2-2, residual de B-2): una línea que ENCADENA >= 2 palabras-marcador DISTINTAS
# separadas SOLO por `/`, `,`, `|` o espacios («# Busca marcadores TODO/FIXME/HACK en el código»)
# enumera la convención léxica, no anota una tarea — no hay `fichero:línea` al que atribuírsela.
# Si entre dos palabras-marcador hay CUALQUIER OTRA COSA (letras, `:`, texto), la cadena se corta
# ahí y NO es enumeración: «# TODO: quitar el FIXME de abajo» tiene "quitar el" entre TODO y
# FIXME → sigue siendo un TODO real (uno solo, como ya decidía `_tipo_marcador`), no una
# enumeración de dos. Igual con «TODO: unificar `a.py`, `b.py`» (una sola palabra-marcador, no
# encadena con otra).
_MARCADOR_WORD_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
_SOLO_SEPARADORES_RE = re.compile(r"^[\s/,|]+$")


def _es_enumeracion_de_palabras_marcador(raw):
    """True si `raw` encadena 2+ palabras-marcador DISTINTAS separadas únicamente por `/`, `,`,
    `|` o espacios (enumeración de la convención, no una anotación real)."""
    matches = list(_MARCADOR_WORD_RE.finditer(raw))
    if len(matches) < 2:
        return False
    vistas = {matches[0].group(1)}
    for previo, actual in zip(matches, matches[1:]):
        entre = raw[previo.end():actual.start()]
        if _SOLO_SEPARADORES_RE.match(entre):
            vistas.add(actual.group(1))
            if len(vistas) >= 2:
                return True
        else:
            vistas = {actual.group(1)}
    return False


# El propio detector se menciona a sí mismo en su docstring y su código («TODO/FIXME/HACK»):
# excluido del recuento de marcadores (no de las otras tres medidas) por RUTA REAL del propio
# script (`os.path.realpath(__file__)`) EN EJECUCIÓN, más una FIRMA DE CONTENIDO (revisión R2,
# R2-1) para cualquier OTRA copia del mismo fichero — necesaria porque un agente ejecuta el kit
# desde la caché del plugin mientras el árbol de este mismo repo tiene su propia copia de
# `code-health.py`: son rutas reales distintas, así que `realpath(__file__)` sólo excluye la
# copia EN EJECUCIÓN y la del repo vuelve a contarse (falso positivo). La firma es un literal
# fijo (`FIRMA_DETECTOR`) que aparece en la primera línea del docstring del detector real; se
# busca solo en ficheros cuyo basename sea `code-health.py` (barato) y solo en sus primeras
# líneas, así que un `code-health.py` de un proyecto CONSUMIDOR que no lleve esa firma exacta
# SÍ se sigue contando (revisión R1, B-6: antes comparaba por `os.path.basename` a secas, que
# excluía cualquier fichero con ese nombre en cualquier ruta, firma o no).
FIRMA_DETECTOR = "code-health.py — informe DETERMINISTA"
_FIRMA_MAX_LINEAS = 10
DETECTOR_PROPIO = os.path.realpath(__file__)
GIT_TIMEOUT = 30


def _es_detector_propio(path_real, basename, lines):
    """True si `path_real` es la copia del detector EN EJECUCIÓN, o si `basename` es
    `code-health.py` y sus primeras `_FIRMA_MAX_LINEAS` líneas llevan `FIRMA_DETECTOR` (otra
    copia del mismo script, p. ej. la del árbol del repo vista desde la caché del plugin)."""
    if path_real == DETECTOR_PROPIO:
        return True
    if basename != "code-health.py":
        return False
    return any(FIRMA_DETECTOR in ln for ln in lines[:_FIRMA_MAX_LINEAS])

# Lenguajes: comentario de línea, ¿anidamiento por llaves?, regex de cabecera de función.
LANG = {
    "py":   {"comment": "#",  "braces": False,
             "func": re.compile(r"^\s*(async\s+)?def\s+\w+\s*\(")},
    "rb":   {"comment": "#",  "braces": False,
             "func": re.compile(r"^\s*def\s+[\w.?!=\[\]<>+\-*/%]+")},
    "js":   {"comment": "//", "braces": True,
             "func": re.compile(r"^\s*(export\s+)?(default\s+)?(async\s+)?function\b|^\s*(const|let|var)\s+\w+\s*=\s*(async\s*)?(\([^)]*\)|\w+)\s*=>|^\s*(async\s+)?[\w$]+\s*\([^)]*\)\s*\{\s*$")},
    "php":  {"comment": "//", "braces": True,
             "func": re.compile(r"^\s*(public|private|protected|static|final|abstract|\s)*\s*function\s+\w+\s*\(")},
    "go":   {"comment": "//", "braces": True, "func": re.compile(r"^\s*func\b")},
    "java": {"comment": "//", "braces": True,
             "func": re.compile(r"^\s*(public|private|protected|static|final|abstract|synchronized|\s)*[\w<>\[\],\s]+\s+\w+\s*\([^)]*\)\s*(throws\s+[\w.,\s]+)?\s*\{\s*$")},
    "cs":   {"comment": "//", "braces": True,
             "func": re.compile(r"^\s*(public|private|protected|internal|static|virtual|override|async|\s)*[\w<>\[\],\s]+\s+\w+\s*\([^)]*\)\s*(where\s+[^{]+)?\s*\{?\s*$")},
    "kt":   {"comment": "//", "braces": True, "func": re.compile(r"^\s*(\w+\s+)*fun\s+")},
    "rs":   {"comment": "//", "braces": True, "func": re.compile(r"^\s*(pub(\([^)]*\))?\s+)?(async\s+)?fn\s+\w+")},
}
for alias, base in (("ts", "js"), ("tsx", "js"), ("jsx", "js")):
    LANG[alias] = LANG[base]

_IDENT = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_NUM = re.compile(r"\b\d+(\.\d+)?\b")
_STR = re.compile(r"(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*')")


# ------------------------------------------------------------------ recorrido

def _bajo_prefijo(rel, prefijos):
    """`rel` (con `/`) cae bajo alguno de `prefijos` (normalizados, sin `/` inicial ni final)."""
    return any(rel == pre or rel.startswith(pre + "/") for pre in prefijos)


def ficheros(root, langs, exclude_tests, exclude_paths=()):
    prefijos = [p.strip().strip("/\\").replace(os.sep, "/") for p in exclude_paths if p.strip()]
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in EXCLUDE_DIRS and not d.startswith("."))
        for fn in sorted(fns):
            ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
            if ext not in langs:
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if exclude_tests and TEST_RE.search(rel):
                continue
            if prefijos and _bajo_prefijo(rel, prefijos):
                continue
            out.append((rel, p, ext))
    return out


def leer(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def sin_comentario(line, marker):
    """Quita el comentario de línea (fuera de cadenas) — aproximación suficiente para shingles.

    Atajo (H-37, T-16): sin el marcador la línea sale entera, y sin comillas se corta en el primer
    marcador; solo una línea con comillas y marcador se recorre carácter a carácter (antes, todas:
    10 s del informe en este repo). Mismo resultado en los dos casos."""
    if marker not in line:
        return str(line)
    if '"' not in line and "'" not in line:
        return str(line)[:line.find(marker)]
    out, i, q = [], 0, None
    while i < len(line):
        c = line[i]
        if q:
            out.append(c)
            if c == "\\" and i + 1 < len(line):
                out.append(line[i + 1])
                i += 1
            elif c == q:
                q = None
        elif c in "\"'":
            q = c
            out.append(c)
        elif line.startswith(marker, i):
            break
        else:
            out.append(c)
        i += 1
    return "".join(out)


def normaliza(line):
    line = _STR.sub("str", line)
    line = _NUM.sub("num", line)
    line = _IDENT.sub(lambda m: m.group(0) if m.group(0) in ("str", "num") else "id", line)
    return re.sub(r"\s+", "", line)


def lineas_codigo(lines, ext, plazo=None):
    """[(nº línea 1-based, normalizada)] de las líneas de código no vacías ni comentario. Con `plazo`
    (time.monotonic) se interrumpe con `PlazoAgotado` cada 2.048 líneas: un fichero enorme no retiene el análisis."""
    marker = LANG[ext]["comment"]
    out = []
    for i, raw in enumerate(lines, 1):
        if plazo is not None and i % 2048 == 0 and time.monotonic() > plazo:
            raise PlazoAgotado()
        s = sin_comentario(raw, marker).strip()
        if not s or s in "{}()[];" or s.startswith(("/*", "*", "*/")):
            continue
        out.append((i, normaliza(s)))
    return out


# ------------------------------------------------------------------ 1. duplicados

# --8<-- shingles (ventana deslizante) COMPARTIDOS -- REPLICADO LITERAL en skills/code-health/scripts/code-health.py (canonico) y skills/training-data-services/scripts/dedup.py (ADR-016)
def shingles(unidades, window):
    """Shingles de `window` unidades consecutivas (lineas normalizadas, palabras...), en orden, como
    la PROPIA cadena unida por `\\n` (nunca `hash()`: determinista entre procesos, PYTHONHASHSEED)."""
    return ["\n".join(unidades[k:k + window]) for k in range(len(unidades) - window + 1)]
# --8<-- fin shingles (ventana deslizante) COMPARTIDOS


def _agotado(plazo):
    return plazo is not None and time.monotonic() > plazo


def _diversas(occ, n):
    """Hasta `n` ocurrencias eligiendo PRIMERO una por fichero (en orden) y rellenando con las repetidas:
    las `n` primeras podían ser todas del mismo fichero y se perdía la duplicación entre ficheros (gap 18)."""
    vistos, elegidas, resto = set(), [], []
    for o in occ:
        if o[0] not in vistos:
            vistos.add(o[0])
            elegidas.append(o)
        else:
            resto.append(o)
    if len(elegidas) < n:
        elegidas += resto[:n - len(elegidas)]
    return elegidas[:n]


_DESPLAZA = 1 << 32      # clave de par = ka * _DESPLAZA + kb (un entero por par en vez de una tupla)


def duplicados(cod, window, top, plazo=None, max_occ=MAX_OCURRENCIAS_DEFAULT, max_pares=MAX_PARES_DEFAULT):
    """cod: {rel: [(nº, norm)]}. Shingles de `window` líneas → pares entre ficheros distintos.
    `plazo` (time.monotonic) corta el emparejado; `max_occ` acota las ocurrencias que se emparejan por
    ventana (0 = sin tope; se eligen de ficheros distintos primero) y `max_pares` el total de pares
    retenidos (0 = sin tope). En los tres casos el resultado lleva `parcial: True`. Si el plazo ya había
    vencido antes de emparejar nada, `pct` es None (sin medir), no un 0 % presentado como mínimo."""
    idx = defaultdict(list)
    parcial = False
    sin_tiempo = False
    recortadas = 0
    if _agotado(plazo):
        parcial = sin_tiempo = True       # plazo ya vencido: nada que medir
    for rel, ls in cod.items():
        if _agotado(plazo):
            parcial = sin_tiempo = True
            break
        for k, h in enumerate(shingles([n for _, n in ls], window)):
            idx[h].append((rel, k))
    pares = defaultdict(set)          # (relA, relB) → {kA * _DESPLAZA + kB}
    n_pares = 0
    n_mismo = 0                       # pares del MISMO fichero: no se retienen pero cuestan y cuentan para el tope
    n_iter = 0
    pares_tope = False
    plazo_vencido = False
    emparejadas = 0
    for n_h, (h, occ) in enumerate(idx.items()):
        if n_h % 512 == 0 and _agotado(plazo):
            parcial = sin_tiempo = True
            break
        if len(occ) < 2:
            continue
        emparejadas += 1
        if max_occ and len(occ) > max_occ:
            occ = _diversas(occ, max_occ)
            recortadas += 1
            parcial = True
        for a in range(len(occ)):
            for b in range(a + 1, len(occ)):
                (ra, ka), (rb, kb) = occ[a], occ[b]
                n_iter += 1
                if n_iter % 4096 == 0 and _agotado(plazo):
                    parcial = sin_tiempo = True
                    plazo_vencido = True
                    break
                if ra == rb:
                    n_mismo += 1
                    if max_pares and n_pares + n_mismo >= max_pares:
                        pares_tope = parcial = True
                        break
                    continue
                if (rb, kb) < (ra, ka):
                    ra, ka, rb, kb = rb, kb, ra, ka
                conj = pares[(ra, rb)]
                clave = ka * _DESPLAZA + kb
                if clave in conj:
                    continue
                if max_pares and n_pares + n_mismo >= max_pares:
                    pares_tope = parcial = True
                    break
                conj.add(clave)
                n_pares += 1
            if pares_tope or plazo_vencido:
                break
        if pares_tope or plazo_vencido:
            break
    bloques = []
    cubiertas = defaultdict(set)
    for (ra, rb), ks in pares.items():
        ks = sorted(ks)
        i = 0
        while i < len(ks):
            ka, kb = divmod(ks[i], _DESPLAZA)
            j = i
            while j + 1 < len(ks) and ks[j + 1] == ks[j] + _DESPLAZA + 1:
                j += 1
            n = window + (j - i)
            for t in range(n):
                cubiertas[ra].add(cod[ra][ka + t][0])
                cubiertas[rb].add(cod[rb][kb + t][0])
            bloques.append({"a": f"{ra}:{cod[ra][ka][0]}", "b": f"{rb}:{cod[rb][kb][0]}", "lineas": n})
            i = j + 1
    total = sum(len(v) for v in cod.values())
    dup = sum(len(v) for v in cubiertas.values())
    bloques.sort(key=lambda x: (-x["lineas"], x["a"], x["b"]))
    sin_medir = sin_tiempo and emparejadas == 0
    return {"bloques": len(bloques), "lineas_codigo": total, "lineas_duplicadas": dup,
            "pct": None if sin_medir else (round(100.0 * dup / total, 1) if total else 0.0),
            "top": bloques[:top], "parcial": parcial, "recortadas": recortadas,
            "pares": n_pares, "pares_tope": pares_tope, "sin_medir": sin_medir}


# ------------------------------------------------------------------ 2. tamaño / complejidad

def profundidad(lines, ext):
    if LANG[ext]["braces"]:
        d = m = 0
        marker = LANG[ext]["comment"]
        for raw in lines:
            s = sin_comentario(raw, marker)
            s = _STR.sub("", s)
            for c in s:
                if c == "{":
                    d += 1
                    m = max(m, d)
                elif c == "}":
                    d = max(0, d - 1)
        return m
    # Indentación: solo cuentan las líneas que ABREN cuerpo (la anterior es una sentencia compuesta
    # que termina en `:` — o `do`/`then`/`else`/`begin` en Ruby), así las continuaciones alineadas
    # de una llamada larga y las líneas de un docstring no inflan la profundidad.
    marker = LANG[ext]["comment"]
    opener = (re.compile(r"^\s*(async\s+def|def|class|if|elif|else|for|while|with|try|except|finally|match|case)\b.*:\s*$")
              if ext == "py" else re.compile(r"(\bdo|\bthen|\belse|\bbegin|^\s*(def|class|module|if|unless|while|until|case|begin)\b.*)\s*$"))
    prev, cuerpos, en_doc = "", [], False
    for raw in lines:
        if ext == "py" and (raw.count('"""') % 2 == 1 or raw.count("'''") % 2 == 1):
            en_doc = not en_doc           # el docstring no cuenta como cuerpo; `prev` se conserva
            continue
        if en_doc:
            continue
        s = sin_comentario(raw, marker).rstrip()
        if not s.strip():
            continue
        ind = len(raw.expandtabs(4)) - len(raw.expandtabs(4).lstrip(" "))
        if opener.search(prev):
            cuerpos.append(ind)
        prev = s
    if not cuerpos:
        return 0
    unit = min((i for i in cuerpos if i > 0), default=4) or 4
    return max(cuerpos) // unit


def funciones_largas(rel, lines, ext, umbral):
    fre = LANG[ext]["func"]
    marker = LANG[ext]["comment"]
    cab = [(i, len(raw) - len(raw.lstrip()), raw.strip()) for i, raw in enumerate(lines, 1)
           if fre.match(raw) and not raw.lstrip().startswith(marker)]
    out = []
    for n, (i, ind, texto) in enumerate(cab):
        fin = len(lines)
        for j, ind2, _ in cab[n + 1:]:
            if ind2 <= ind:
                fin = j - 1
                break
        cuerpo = [raw for raw in lines[i:fin]
                  if raw.strip() and raw.strip() not in "{}()[];" and not raw.lstrip().startswith(marker)]
        if len(cuerpo) > umbral:
            nombre = re.sub(r"\s+", " ", texto)[:70]
            out.append({"fichero": f"{rel}:{i}", "funcion": nombre, "lineas": len(cuerpo)})
    return out


def tamano(src, umbral, top):
    fich, largas = [], []
    for rel, lines, ext in src:
        cod = [raw for raw in lines if raw.strip() and not raw.lstrip().startswith(LANG[ext]["comment"])]
        fich.append({"fichero": rel, "lineas": len(cod), "anidamiento": profundidad(lines, ext)})
        largas += funciones_largas(rel, lines, ext, umbral)
    fich.sort(key=lambda f: (-f["lineas"], f["fichero"]))
    largas.sort(key=lambda f: (-f["lineas"], f["fichero"]))
    return {"ficheros": len(fich), "lineas": sum(f["lineas"] for f in fich),
            "anidamiento_max": max((f["anidamiento"] for f in fich), default=0),
            "funciones_largas": len(largas), "umbral_funcion": umbral,
            "top_ficheros": fich[:top], "top_funciones": largas[:top]}


# ------------------------------------------------------------------ git: hotspots y antigüedad

def git(root, *args, timeout=GIT_TIMEOUT, estado=None):
    """Salida de `git`, o None si falla. Con `estado` (lista) se anota POR QUÉ: `cortado` (plazo vencido,
    `OSError` —p. ej. línea de comandos demasiado larga en Windows—) o `error` (git salió con código ≠ 0, como
    `blame` de un fichero sin versionar). Solo `cortado` deja un informe incompleto."""
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError):
        if estado is not None:
            estado.append("cortado")
        return None
    if r.returncode != 0 and estado is not None:
        estado.append("error")
    return r.stdout if r.returncode == 0 else None


def hay_git(root):
    return git(root, "rev-parse", "--is-inside-work-tree") is not None


def excluidos_versionados(root, exclude_paths=(), langs=None):
    """Ficheros VERSIONADOS en git (cualquier extensión) bajo un directorio de terceros o de build
    que el análisis excluye por defecto (`VENDOR_BUILD_DIRS`): código incrustado o artefactos
    commiteados que ninguna medida ve. Solo se cuentan, agrupados por el prefijo hasta el primer
    directorio excluido; no se analizan. Las rutas bajo `--exclude-path` no cuentan (exclusión
    deliberada). Las carpetas OCULTAS versionadas (`.claude/`, `.github/`…) también salen del análisis: se
    cuentan solo los ficheros de código (extensión de `langs`; por defecto, la de cualquier lenguaje soportado).
    None sin git."""
    out = git(root, "ls-files", "-z")
    if out is None:
        return None
    prefijos = [p.strip().strip("/\\").replace(os.sep, "/") for p in exclude_paths if p.strip()]
    por_dir = defaultdict(int)
    codigo = set(langs) if langs else set(LANG)
    for rel in out.split("\0"):
        if not rel or (prefijos and _bajo_prefijo(rel, prefijos)):
            continue
        partes = rel.split("/")[:-1]
        nombre = rel.rsplit("/", 1)[-1]
        ext = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
        for i, parte in enumerate(partes):
            if parte in VENDOR_BUILD_DIRS or (parte.startswith(".") and ext in codigo):
                por_dir["/".join(partes[:i + 1]) + "/"] += 1
                break
    return {"total": sum(por_dir.values()), "por_directorio": dict(sorted(por_dir.items()))}


def hotspots(root, since, tam_por_fichero, rels, top):
    log = git(root, "log", f"--since={since} days ago", "--name-only", "--pretty=format:")
    if log is None:
        return None
    prefijo = (git(root, "rev-parse", "--show-prefix") or "").strip()
    cuenta = defaultdict(int)
    for line in log.splitlines():
        p = line.strip()
        if not p:
            continue
        if prefijo and p.startswith(prefijo):
            p = p[len(prefijo):]
        if p in rels:
            cuenta[p] += 1
    out = [{"fichero": p, "cambios": c, "lineas": tam_por_fichero.get(p, 0),
            "puntuacion": round(c * math.log2(tam_por_fichero.get(p, 0) + 1), 1)}
           for p, c in cuenta.items()]
    out.sort(key=lambda h: (-h["puntuacion"], h["fichero"]))
    return {"dias": since, "ficheros_cambiados": len(out), "top": out[:top]}


def edad_dias(root, rel, linea, hoy):
    out = git(root, "blame", "-L", f"{linea},{linea}", "--porcelain", "--", rel)
    if not out:
        return None
    m = re.search(r"^author-time (\d+)$", out, re.M)
    if not m:
        return None
    fecha = _dt.datetime.fromtimestamp(int(m.group(1)), _dt.timezone.utc).date()
    return max(0, (hoy - fecha).days)


_BLAME_CABECERA = re.compile(r"^([0-9a-f]{40}) \d+ (\d+)(?: \d+)?$")


BLAME_L_POR_LLAMADA = 200      # `-L n,n` por subproceso: ~3 KB de argumentos, muy bajo los 32 K de Windows


def edades_dias(root, rel, lineas, hoy, plazo=None, perdidas=None):
    """{línea: edad en días} de varias líneas de UN fichero con `git blame` (varios `-L` por llamada, en
    trozos de `BLAME_L_POR_LLAMADA`; antes, un subproceso por línea: 10 = 4,6 s). Con `plazo`, ningún
    subproceso puede pasarse del tiempo que queda. Si un trozo se CORTA (plazo, `OSError`) o el plazo vence
    entre trozos, sus líneas se suman a `perdidas[0]` (lista de un entero) para que el informe se declare
    parcial; un `git blame` con error (fichero sin versionar) deja esas edades en blanco sin más."""
    res = {}
    for ini in range(0, len(lineas), BLAME_L_POR_LLAMADA):
        trozo = lineas[ini:ini + BLAME_L_POR_LLAMADA]
        if _agotado(plazo):
            if perdidas is not None:
                perdidas[0] += len(lineas) - ini
            break
        args = ["blame", "--porcelain"]
        for n in trozo:
            args += ["-L", f"{n},{n}"]
        args += ["--", rel]
        limite = GIT_TIMEOUT if plazo is None else max(1.0, min(GIT_TIMEOUT, plazo - time.monotonic()))
        estado = []
        out = git(root, *args, timeout=limite, estado=estado)
        if "cortado" in estado and perdidas is not None:
            perdidas[0] += len(trozo)
        if out:
            res.update(_edades_de_blame(out, hoy))
        elif "error" in estado and "cortado" not in estado and _versionado(root, rel):
            # Un solo `-L` fuera de rango (p. ej. un `\x0c` que Python cuenta como salto de línea y git no)
            # hace fallar TODO el trozo: se reintenta línea a línea y lo que siga sin edad marca el informe.
            for pos, n in enumerate(trozo):
                if _agotado(plazo):
                    if perdidas is not None:
                        perdidas[0] += len(trozo) - pos
                    break
                lim = GIT_TIMEOUT if plazo is None else max(1.0, min(GIT_TIMEOUT, plazo - time.monotonic()))
                o1 = git(root, "blame", "--porcelain", "-L", f"{n},{n}", "--", rel, timeout=lim)
                if o1:
                    res.update(_edades_de_blame(o1, hoy))
                if n not in res and perdidas is not None:
                    perdidas[0] += 1
    return res


def _edades_de_blame(out, hoy):
    """{línea: edad en días} de una salida `git blame --porcelain`."""
    sha_de, tiempos, cur, res = {}, {}, None, {}
    for ln in out.splitlines():
        m = _BLAME_CABECERA.match(ln)
        if m:
            cur = m.group(1)
            sha_de[int(m.group(2))] = cur
        elif cur and ln.startswith("author-time "):
            try:
                tiempos[cur] = int(ln.split()[1])
            except (IndexError, ValueError):
                pass
    for n, sha in sha_de.items():
        if sha in tiempos:
            fecha = _dt.datetime.fromtimestamp(tiempos[sha], _dt.timezone.utc).date()
            res[n] = max(0, (hoy - fecha).days)
    return res


def _versionado(root, rel):
    """¿`rel` está versionado en git? Un fichero sin versionar no tiene edad y no es un fallo de medida."""
    return git(root, "ls-files", "--error-unmatch", "--", rel) is not None


def marcadores(root, src, con_git, top, plazo=None):
    hoy = _dt.date.today()
    items = []
    for rel, lines, _ in src:
        p_real = os.path.realpath(os.path.join(root, *rel.split("/")))
        basename = rel.rsplit("/", 1)[-1]
        if _es_detector_propio(p_real, basename, lines):
            continue    # el detector (en ejecución o una copia con su firma) no se cuenta a sí mismo
        for i, raw in enumerate(lines, 1):
            if _es_enumeracion_de_marcadores(raw) or _es_enumeracion_de_palabras_marcador(raw):
                continue   # enumeración de marcadores (entre backticks o encadenados), no una anotación real
            tipo = _tipo_marcador(raw)
            if not tipo:
                continue
            items.append({"fichero": f"{rel}:{i}", "tipo": tipo,
                          "texto": raw.strip()[:90], "edad_dias": None})
    edad_parcial = 0
    if con_git:
        por_fichero = defaultdict(list)
        for it in items:
            rel, _, n = it["fichero"].rpartition(":")
            por_fichero[rel].append((int(n), it))
        for rel, pares_ in por_fichero.items():
            if _agotado(plazo):
                edad_parcial += len(pares_)         # sin tiempo: la edad queda sin calcular, no inventada
                continue
            perdidas = [0]
            edades = edades_dias(root, rel, [n for n, _ in pares_], hoy, plazo, perdidas)
            edad_parcial += perdidas[0]             # blame cortado (plazo, OSError): sin calcular, no inventada
            for n, it in pares_:
                it["edad_dias"] = edades.get(n)
    items.sort(key=lambda t: (-(t["edad_dias"] if t["edad_dias"] is not None else -1), t["fichero"]))
    por_tipo = defaultdict(int)
    for t in items:
        por_tipo[t["tipo"]] += 1
    con_edad = [t["edad_dias"] for t in items if t["edad_dias"] is not None]
    return {"total": len(items), "por_tipo": dict(sorted(por_tipo.items())),
            "edad_max_dias": max(con_edad) if con_edad else None,
            "antiguedad": "git" if con_git else "no disponible (sin git)", "edad_parcial": edad_parcial,
            "top": items[:top]}


# ------------------------------------------------------------------ informe

def analizar(root, langs, window, min_lines, exclude_tests, since, top, exclude_paths=(),
             max_files=0, max_seconds=0, max_occ=MAX_OCURRENCIAS_DEFAULT, max_pares=MAX_PARES_DEFAULT,
             max_bytes=0):
    """`max_files`/`max_seconds`/`max_bytes` (0 = sin tope) acotan el análisis; al alcanzarlos el informe es
    parcial. `max_occ` y `max_pares` acotan el emparejado de duplicados (memoria)."""
    avisos = []
    plazo = time.monotonic() + max_seconds if max_seconds else None
    parcial = False
    motivos = set()          # por qué el informe es parcial: dos parciales solo se comparan si coinciden
    lista = ficheros(root, langs, exclude_tests, exclude_paths)
    if max_files and len(lista) > max_files:
        avisos.append(f"tope de ficheros: se analizan {max_files} de {len(lista)} (orden alfabético de ruta); "
                      "el informe es PARCIAL — acota con `--exclude-path`/`--langs` o sube `--max-files`")
        lista = lista[:max_files]
        parcial = True
        motivos.add("max-files")
    src = []
    cod = {}
    grandes = []
    cortado = False
    for rel, p, ext in lista:
        if _agotado(plazo):
            cortado = True
            break
        if max_bytes:
            try:
                tam_b = os.path.getsize(p)
            except OSError:
                tam_b = 0
            if tam_b > max_bytes:
                grandes.append((rel, tam_b))
                continue
        lines = leer(p)
        if lines is not None:
            try:
                cod[rel] = lineas_codigo(lines, ext, plazo)
            except PlazoAgotado:
                cortado = True
                break
            src.append((rel, lines, ext))
    if cortado:
        avisos.append(f"tope de tiempo ({max_seconds} s): se analizan {len(src)} de {len(lista)} ficheros; "
                      "el informe es PARCIAL — acota con `--exclude-path`/`--langs` o sube `--max-seconds`")
        parcial = True
        motivos.add("tiempo")
    if grandes:
        muestra = ", ".join(f"`{r}` ({t} bytes)" for r, t in grandes[:3]) + (", …" if len(grandes) > 3 else "")
        avisos.append(f"{len(grandes)} ficheros superan {max_bytes} bytes y se omiten ({muestra}): bundles, volcados o "
                      "código generado; el informe es PARCIAL — exclúyelos con `--exclude-path` o sube `--max-bytes`")
        parcial = True
        motivos.add("max-bytes")
    dup = duplicados(cod, window, top, plazo, max_occ, max_pares)
    if dup.get("recortadas"):
        motivos.add("max-occ")
    if dup.get("pares_tope"):
        motivos.add("max-pairs")
    if dup.get("sin_medir") or (dup.get("parcial") and not dup.get("recortadas") and not dup.get("pares_tope")):
        motivos.add("tiempo-duplicados")
    if dup.get("recortadas"):
        avisos.append(f"{dup['recortadas']} ventanas de {window} líneas aparecen más de {max_occ} "
                      "veces (copias casi idénticas, plantillas o código generado): solo se emparejan las primeras "
                      "ocurrencias (de ficheros distintos primero); el % duplicado es un mínimo (informe PARCIAL) — "
                      "excluye lo generado con `--exclude-path` o cambia `--max-occ`")
    if dup.get("pares_tope"):
        avisos.append(f"tope de {max_pares} pares de líneas duplicadas (memoria acotada): se deja de emparejar y el "
                      "% duplicado es un mínimo (informe PARCIAL) — excluye lo generado con `--exclude-path` o sube `--max-pairs`")
    if dup.get("sin_medir"):
        avisos.append("el plazo se agotó antes de buscar duplicados: el % duplicado queda SIN MEDIR (n/d), no es 0 %")
    elif dup.get("parcial") and not dup.get("recortadas") and not dup.get("pares_tope") and not any("tope de tiempo" in a for a in avisos):
        avisos.append(f"tope de tiempo ({max_seconds} s) en la búsqueda de duplicados: el % duplicado es un "
                      "mínimo (informe PARCIAL) — acota con `--exclude-path`/`--langs` o sube `--max-seconds`")
    parcial = parcial or bool(dup.get("parcial"))
    tam = tamano(src, min_lines * 5, top)
    con_git = hay_git(root)
    hs = None
    if con_git:
        hs = hotspots(root, since, {f["fichero"]: f["lineas"] for f in
                                    [{"fichero": rel, "lineas": len(cod[rel])} for rel, _, _ in src]},
                      set(cod), top)
        if hs is None:
            con_git = False
    if not con_git:
        avisos.append("git no disponible o la ruta no es un repositorio: hotspots omitidos y TODO sin antigüedad")
    tod = marcadores(root, src, con_git, top, plazo)
    if tod.get("edad_parcial"):
        avisos.append(f"{tod['edad_parcial']} de {tod['total']} TODO sin antigüedad: `git blame` se cortó por el tope de "
                      f"tiempo ({max_seconds or 'sin tope'} s), por un error del sistema (p. ej. línea de comandos "
                      "demasiado larga) o por un número de línea que git no reconoce (p. ej. un salto de página "
                      "dentro de una línea); el informe es PARCIAL — sube `--max-seconds` o revisa `git`")
        parcial = True
        motivos.add("edad")
    ev = excluidos_versionados(root, exclude_paths, langs) if con_git else None
    if ev and ev["total"]:
        dirs = sorted(ev["por_directorio"].items(), key=lambda kv: (-kv[1], kv[0]))
        lista_dirs = ", ".join(f"`{d}` ({n})" for d, n in dirs[:5]) + (", …" if len(dirs) > 5 else "")
        avisos.append(f"{ev['total']} ficheros versionados en git bajo directorios de terceros, de build u "
                      f"ocultos que el análisis excluye: {lista_dirs}. Código incrustado o artefactos commiteados "
                      "que ninguna medida ve; no se analizan")
    prefijos_norm = sorted({p.strip().strip("/\\").replace(os.sep, "/")
                            for p in exclude_paths if p.strip()})
    return {"ruta": os.path.abspath(root), "fecha": _dt.date.today().isoformat(),
            "parametros": {"langs": sorted(langs), "window": window, "min_lines": min_lines,
                           "exclude_tests": exclude_tests, "since_dias": since,
                           "exclude_path": prefijos_norm},
            "resumen": {"ficheros": tam["ficheros"], "lineas": tam["lineas"],
                        "duplicado_pct": dup["pct"], "bloques_duplicados": dup["bloques"],
                        "funciones_largas": tam["funciones_largas"],
                        "anidamiento_max": tam["anidamiento_max"],
                        "hotspots": hs["ficheros_cambiados"] if hs else None,
                        "todos": tod["total"], "todo_edad_max_dias": tod["edad_max_dias"]},
            "duplicados": dup, "tamano": tam, "hotspots": hs, "marcadores": tod,
            "excluidos_versionados": ev, "avisos": avisos, "parcial": parcial,
            "parcial_motivos": sorted(motivos)}


# Métricas comparables con --baseline: (clave del resumen, «menos es mejor»)
METRICAS = [("duplicado_pct", "% duplicado"), ("bloques_duplicados", "bloques duplicados"),
            ("funciones_largas", "funciones largas"), ("anidamiento_max", "anidamiento máx."),
            ("todos", "TODO/FIXME/HACK"), ("todo_edad_max_dias", "edad máx. TODO (días)"),
            ("lineas", "líneas de código")]


NO_COMPARABLE = "no comparable (los informes no cubren lo mismo: parcial contra completo, o parciales con distinta cobertura)"


def _cobertura(r):
    """Qué cubrió el informe: ficheros y líneas de código medidos (un informe parcial cubre otro conjunto)."""
    res = r.get("resumen") or {}
    return (res.get("ficheros"), res.get("lineas"))


def _motivos(r):
    """Motivos de parcialidad declarados (None en informes anteriores a `parcial_motivos`)."""
    m = r.get("parcial_motivos")
    return tuple(sorted(m)) if isinstance(m, list) else None


def comparar(actual, base):
    """Tendencia por métrica. Un informe PARCIAL (tope de ficheros, de tiempo, de pares…) cubre otro
    conjunto que uno completo, y dos parciales cubren conjuntos distintos salvo que midan lo mismo: sin
    cobertura idéntica (ficheros y líneas), compararlos daría «↓ mejora»/«↑ empeora» falsos."""
    out = []
    pa, pb = bool(actual.get("parcial")), bool(base.get("parcial"))
    incomparable = pa != pb or (pa and pb and (_cobertura(actual) != _cobertura(base)
                                               or _motivos(actual) != _motivos(base)))
    for k, label in METRICAS:
        a, b = actual["resumen"].get(k), (base.get("resumen") or {}).get(k)
        if incomparable:
            out.append({"metrica": label, "antes": b, "ahora": a, "tendencia": NO_COMPARABLE})
            continue
        if a is None or b is None:
            out.append({"metrica": label, "antes": b, "ahora": a, "tendencia": "n/d"})
            continue
        if k == "lineas":
            tend = "="  if a == b else ("↑ crece" if a > b else "↓ decrece")
        else:
            tend = "= igual" if a == b else ("↓ mejora" if a < b else "↑ empeora")
        out.append({"metrica": label, "antes": b, "ahora": a, "tendencia": tend})
    return out


def _pct(v):
    return "n/d" if v is None else f"{v} %"


def md(r):
    s, top = r["resumen"], []
    L = [f"# Salud del código — `{r['ruta']}` ({r['fecha']})", "",
         f"**{s['ficheros']} ficheros · {s['lineas']} líneas de código** · duplicado **{_pct(s['duplicado_pct'])}** "
         f"({s['bloques_duplicados']} bloques) · funciones largas **{s['funciones_largas']}** "
         f"(> {r['tamano']['umbral_funcion']} líneas) · anidamiento máx. **{s['anidamiento_max']}** · "
         f"TODO/FIXME/HACK **{s['todos']}**"
         + (f" (el más viejo: {s['todo_edad_max_dias']} días)" if s["todo_edad_max_dias"] is not None else "")
         + (f" · hotspots {s['hotspots']} ficheros cambiados en {r['hotspots']['dias']} días" if r["hotspots"] else ""), ""]
    excl = r["parametros"].get("exclude_path") or []
    L.append(f"Parámetros: lenguajes `{','.join(r['parametros']['langs'])}` · ventana {r['parametros']['window']} "
             f"líneas · tests {'excluidos' if r['parametros']['exclude_tests'] else 'incluidos'}"
             + (f" · rutas excluidas `{','.join(excl)}`" if excl else "") + ". "
             "Todas las medidas son **heurísticas** (regex y tokens, no un parser): sirven para ordenar y "
             "comparar, no para juzgar una línea concreta.")
    for a in r["avisos"]:
        L.append(f"\n> ⚠️ {a}")
    if r.get("baseline"):
        L += ["", "## Comparación con baseline", "", "| Métrica | Antes | Ahora | Tendencia |", "|---|---|---|---|"]
        L += [f"| {c['metrica']} | {c['antes']} | {c['ahora']} | {c['tendencia']} |" for c in r["baseline"]]
    d = r["duplicados"]
    L += ["", f"## 1. Duplicados — {_pct(d['pct'])} de {d['lineas_codigo']} líneas ({d['bloques']} bloques entre ficheros distintos)", ""]
    if d["top"]:
        L += ["| Líneas | Fichero A | Fichero B |", "|---|---|---|"]
        L += [f"| {b['lineas']} | `{b['a']}` | `{b['b']}` |" for b in d["top"]]
    else:
        L.append("_Sin bloques duplicados con la ventana actual._")
    t = r["tamano"]
    L += ["", f"## 2. Tamaño y complejidad aproximada — {t['funciones_largas']} funciones > {t['umbral_funcion']} líneas", ""]
    if t["top_funciones"]:
        L += ["| Líneas | Función | Dónde |", "|---|---|---|"]
        L += [f"| {f['lineas']} | `{f['funcion']}` | `{f['fichero']}` |" for f in t["top_funciones"]]
    else:
        L.append("_Ninguna función supera el umbral._")
    L += ["", "Ficheros más grandes (líneas · anidamiento máx.):", ""]
    L += [f"- `{f['fichero']}` — {f['lineas']} · {f['anidamiento']}" for f in t["top_ficheros"]]
    L += ["", "## 3. Hotspots (grandes Y que cambian mucho)", ""]
    h = r["hotspots"]
    if h is None:
        L.append("_Omitido: sin git._")
    elif not h["top"]:
        L.append(f"_Sin cambios en los últimos {h['dias']} días para los ficheros analizados._")
    else:
        L += [f"| Puntuación | Cambios ({h['dias']} d) | Líneas | Fichero |", "|---|---|---|---|"]
        L += [f"| {x['puntuacion']} | {x['cambios']} | {x['lineas']} | `{x['fichero']}` |" for x in h["top"]]
    m = r["marcadores"]
    L += ["", f"## 4. TODO/FIXME/HACK/XXX — {m['total']} (antigüedad: {m['antiguedad']})", ""]
    if m["top"]:
        L += ["| Edad (días) | Tipo | Dónde | Texto |", "|---|---|---|---|"]
        for x in m["top"]:
            edad = x["edad_dias"] if x["edad_dias"] is not None else "—"
            texto = x["texto"].replace("|", "\\|")
            L.append(f"| {edad} | {x['tipo']} | `{x['fichero']}` | {texto} |")
    else:
        L.append("_Sin marcadores._")
    return "\n".join(L) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("ruta")
    p.add_argument("--json", action="store_true")
    p.add_argument("--min-lines", type=int, default=6, help="función larga = > min-lines × 5 líneas (default 6 → 30)")
    p.add_argument("--langs", default=LANGS_DEFAULT)
    p.add_argument("--window", type=int, default=8)
    p.add_argument("--exclude-tests", action="store_true")
    p.add_argument("--exclude-path", action="append", default=[], metavar="PREFIJO",
                    help="prefijo relativo a la raíz a excluir (repetible; p.ej. interop); default sin exclusiones")
    p.add_argument("--since", type=int, default=90, help="días de git log para hotspots")
    p.add_argument("--baseline", help="informe --json anterior con el que comparar")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--max-files", type=int, default=MAX_FICHEROS_DEFAULT,
                   help=f"tope de ficheros a analizar (default {MAX_FICHEROS_DEFAULT}; 0 = sin tope); al alcanzarlo "
                        "el informe es parcial y lo avisa")
    p.add_argument("--max-occ", type=int, default=MAX_OCURRENCIAS_DEFAULT,
                   help=f"ocurrencias que se emparejan por ventana de líneas (default {MAX_OCURRENCIAS_DEFAULT}; 0 = sin "
                        "tope: más memoria y tiempo con plantillas o código generado)")
    p.add_argument("--max-pairs", type=int, default=MAX_PARES_DEFAULT,
                   help=f"tope TOTAL de pares duplicados retenidos (default {MAX_PARES_DEFAULT}; 0 = sin tope); informe parcial al alcanzarlo")
    p.add_argument("--max-bytes", type=int, default=MAX_BYTES_DEFAULT,
                   help=f"se omite (con aviso) todo fichero de código mayor que esto (default {MAX_BYTES_DEFAULT}; 0 = sin tope)")
    p.add_argument("--max-seconds", type=float, default=MAX_SEGUNDOS_DEFAULT,
                   help=f"tope de segundos del análisis (default {MAX_SEGUNDOS_DEFAULT}; 0 = sin tope); informe parcial si se agota")
    a = p.parse_args(argv)
    if not os.path.isdir(a.ruta):
        print(f"code-health: la ruta no existe o no es un directorio: {a.ruta}", file=sys.stderr)
        return 2
    base = None
    if a.baseline:
        try:
            base = json.load(open(a.baseline, encoding="utf-8"))
            if not isinstance(base, dict) or "resumen" not in base:
                raise ValueError("no es un informe de code-health (falta `resumen`)")
        except (OSError, ValueError) as e:
            print(f"code-health: baseline ilegible: {e}", file=sys.stderr)
            return 2
    langs = {x.strip().lower().lstrip(".") for x in a.langs.split(",") if x.strip()} & set(LANG)
    r = analizar(a.ruta, langs, max(2, a.window), max(1, a.min_lines), a.exclude_tests, a.since, a.top,
                 exclude_paths=a.exclude_path, max_files=a.max_files, max_seconds=a.max_seconds, max_occ=max(0, a.max_occ),
                 max_pares=max(0, a.max_pairs), max_bytes=max(0, a.max_bytes))
    if base is not None:
        r["baseline"] = comparar(r, base)
        r["baseline_fecha"] = base.get("fecha")
        if any(c["tendencia"] == NO_COMPARABLE for c in r["baseline"]):
            if bool(r["parcial"]) != bool(base.get("parcial")):
                r["avisos"].append("baseline: " + ("este informe" if r["parcial"] else "el baseline") + " es PARCIAL y el otro "
                                   "completo (informe parcial = otro conjunto de ficheros): las tendencias salen «no comparable»; repite los dos con los mismos topes")
            else:
                r["avisos"].append("baseline: los dos informes son PARCIALES con distinta cobertura o motivo de parcialidad (ficheros, líneas o topes "
                                   "medidos): las tendencias salen «no comparable»; repite los dos con los mismos topes")
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else md(r), end="" if not a.json else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
