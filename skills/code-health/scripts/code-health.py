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

Uso:
  code-health.py <ruta> [--json] [--min-lines 6] [--langs py,js,ts,…] [--window 8]
                        [--exclude-tests] [--since 90] [--baseline informe.json] [--top 10]
Exit: 0 siempre (informe emitido) · 2 error de uso (ruta inexistente, baseline ilegible).
"""
import argparse
import datetime as _dt
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict

LANGS_DEFAULT = "py,js,ts,tsx,jsx,php,go,java,rb,cs,kt,rs"
EXCLUDE_DIRS = {"vendor", "node_modules", "dist", "build", ".git", "__pycache__", ".venv", "venv",
                "target", ".next", "coverage", ".idea", ".vscode"}
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec|specs)(/|$)|(^|/)test_[^/]+\.py$|[._-](test|spec)\.[a-z]+$")
# Marcador = la palabra seguida de `:`/`(`/`-` o al COMIENZO del comentario («# TODO revisar»). Así la
# palabra castellana «TODO» en mayúsculas dentro de una frase («el histórico TODO como ventana») no cuenta.
TODO_RE = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b(?=\s*[:(\-—]|\s*$)|(?:^|(?<=[#/*!]))\s*(TODO|FIXME|HACK|XXX)\b")
GIT_TIMEOUT = 30

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

def ficheros(root, langs, exclude_tests):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in EXCLUDE_DIRS and not d.startswith(".git"))
        for fn in sorted(fns):
            ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
            if ext not in langs:
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if exclude_tests and TEST_RE.search(rel):
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
    """Quita el comentario de línea (fuera de cadenas) — aproximación suficiente para shingles."""
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


def lineas_codigo(lines, ext):
    """[(nº línea 1-based, normalizada)] de las líneas de código no vacías ni comentario."""
    marker = LANG[ext]["comment"]
    out = []
    for i, raw in enumerate(lines, 1):
        s = sin_comentario(raw, marker).strip()
        if not s or s in "{}()[];" or s.startswith(("/*", "*", "*/")):
            continue
        out.append((i, normaliza(s)))
    return out


# ------------------------------------------------------------------ 1. duplicados

def duplicados(cod, window, top):
    """cod: {rel: [(nº, norm)]}. Shingles de `window` líneas → pares entre ficheros distintos."""
    idx = defaultdict(list)
    for rel, ls in cod.items():
        for k in range(len(ls) - window + 1):
            h = "\n".join(n for _, n in ls[k:k + window])     # la propia cadena: determinista entre procesos
            idx[h].append((rel, k))
    pares = defaultdict(set)          # (relA, relB) → {(kA, kB)}
    for h, occ in idx.items():
        if len(occ) < 2:
            continue
        for a in range(len(occ)):
            for b in range(a + 1, len(occ)):
                (ra, ka), (rb, kb) = occ[a], occ[b]
                if ra == rb:
                    continue
                if (rb, kb) < (ra, ka):
                    ra, ka, rb, kb = rb, kb, ra, ka
                pares[(ra, rb)].add((ka, kb))
    bloques = []
    cubiertas = defaultdict(set)
    for (ra, rb), ks in pares.items():
        ks = sorted(ks)
        i = 0
        while i < len(ks):
            ka, kb = ks[i]
            j = i
            while j + 1 < len(ks) and ks[j + 1] == (ks[j][0] + 1, ks[j][1] + 1):
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
    return {"bloques": len(bloques), "lineas_codigo": total, "lineas_duplicadas": dup,
            "pct": round(100.0 * dup / total, 1) if total else 0.0, "top": bloques[:top]}


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

def git(root, *args):
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True,
                           timeout=GIT_TIMEOUT, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def hay_git(root):
    return git(root, "rev-parse", "--is-inside-work-tree") is not None


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


def marcadores(root, src, con_git, top):
    hoy = _dt.date.today()
    items = []
    for rel, lines, _ in src:
        for i, raw in enumerate(lines, 1):
            m = TODO_RE.search(raw)
            if not m:
                continue
            item = {"fichero": f"{rel}:{i}", "tipo": m.group(1) or m.group(2),
                    "texto": raw.strip()[:90], "edad_dias": None}
            if con_git:
                item["edad_dias"] = edad_dias(root, rel, i, hoy)
            items.append(item)
    items.sort(key=lambda t: (-(t["edad_dias"] if t["edad_dias"] is not None else -1), t["fichero"]))
    por_tipo = defaultdict(int)
    for t in items:
        por_tipo[t["tipo"]] += 1
    con_edad = [t["edad_dias"] for t in items if t["edad_dias"] is not None]
    return {"total": len(items), "por_tipo": dict(sorted(por_tipo.items())),
            "edad_max_dias": max(con_edad) if con_edad else None,
            "antiguedad": "git" if con_git else "no disponible (sin git)", "top": items[:top]}


# ------------------------------------------------------------------ informe

def analizar(root, langs, window, min_lines, exclude_tests, since, top):
    avisos = []
    lista = ficheros(root, langs, exclude_tests)
    src = []
    for rel, p, ext in lista:
        lines = leer(p)
        if lines is not None:
            src.append((rel, lines, ext))
    cod = {rel: lineas_codigo(lines, ext) for rel, lines, ext in src}
    dup = duplicados(cod, window, top)
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
    tod = marcadores(root, src, con_git, top)
    return {"ruta": os.path.abspath(root), "fecha": _dt.date.today().isoformat(),
            "parametros": {"langs": sorted(langs), "window": window, "min_lines": min_lines,
                           "exclude_tests": exclude_tests, "since_dias": since},
            "resumen": {"ficheros": tam["ficheros"], "lineas": tam["lineas"],
                        "duplicado_pct": dup["pct"], "bloques_duplicados": dup["bloques"],
                        "funciones_largas": tam["funciones_largas"],
                        "anidamiento_max": tam["anidamiento_max"],
                        "hotspots": hs["ficheros_cambiados"] if hs else None,
                        "todos": tod["total"], "todo_edad_max_dias": tod["edad_max_dias"]},
            "duplicados": dup, "tamano": tam, "hotspots": hs, "marcadores": tod, "avisos": avisos}


# Métricas comparables con --baseline: (clave del resumen, «menos es mejor»)
METRICAS = [("duplicado_pct", "% duplicado"), ("bloques_duplicados", "bloques duplicados"),
            ("funciones_largas", "funciones largas"), ("anidamiento_max", "anidamiento máx."),
            ("todos", "TODO/FIXME/HACK"), ("todo_edad_max_dias", "edad máx. TODO (días)"),
            ("lineas", "líneas de código")]


def comparar(actual, base):
    out = []
    for k, label in METRICAS:
        a, b = actual["resumen"].get(k), (base.get("resumen") or {}).get(k)
        if a is None or b is None:
            out.append({"metrica": label, "antes": b, "ahora": a, "tendencia": "n/d"})
            continue
        if k == "lineas":
            tend = "="  if a == b else ("↑ crece" if a > b else "↓ decrece")
        else:
            tend = "= igual" if a == b else ("↓ mejora" if a < b else "↑ empeora")
        out.append({"metrica": label, "antes": b, "ahora": a, "tendencia": tend})
    return out


def md(r):
    s, top = r["resumen"], []
    L = [f"# Salud del código — `{r['ruta']}` ({r['fecha']})", "",
         f"**{s['ficheros']} ficheros · {s['lineas']} líneas de código** · duplicado **{s['duplicado_pct']} %** "
         f"({s['bloques_duplicados']} bloques) · funciones largas **{s['funciones_largas']}** "
         f"(> {r['tamano']['umbral_funcion']} líneas) · anidamiento máx. **{s['anidamiento_max']}** · "
         f"TODO/FIXME/HACK **{s['todos']}**"
         + (f" (el más viejo: {s['todo_edad_max_dias']} días)" if s["todo_edad_max_dias"] is not None else "")
         + (f" · hotspots {s['hotspots']} ficheros cambiados en {r['hotspots']['dias']} días" if r["hotspots"] else ""), ""]
    L.append(f"Parámetros: lenguajes `{','.join(r['parametros']['langs'])}` · ventana {r['parametros']['window']} "
             f"líneas · tests {'excluidos' if r['parametros']['exclude_tests'] else 'incluidos'}. "
             "Todas las medidas son **heurísticas** (regex y tokens, no un parser): sirven para ordenar y "
             "comparar, no para juzgar una línea concreta.")
    for a in r["avisos"]:
        L.append(f"\n> ⚠️ {a}")
    if r.get("baseline"):
        L += ["", "## Comparación con baseline", "", "| Métrica | Antes | Ahora | Tendencia |", "|---|---|---|---|"]
        L += [f"| {c['metrica']} | {c['antes']} | {c['ahora']} | {c['tendencia']} |" for c in r["baseline"]]
    d = r["duplicados"]
    L += ["", f"## 1. Duplicados — {d['pct']} % de {d['lineas_codigo']} líneas ({d['bloques']} bloques entre ficheros distintos)", ""]
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
    p.add_argument("--since", type=int, default=90, help="días de git log para hotspots")
    p.add_argument("--baseline", help="informe --json anterior con el que comparar")
    p.add_argument("--top", type=int, default=10)
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
    r = analizar(a.ruta, langs, max(2, a.window), max(1, a.min_lines), a.exclude_tests, a.since, a.top)
    if base is not None:
        r["baseline"] = comparar(r, base)
        r["baseline_fecha"] = base.get("fecha")
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else md(r), end="" if not a.json else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
