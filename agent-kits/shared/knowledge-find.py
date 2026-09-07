#!/usr/bin/env python3
"""
knowledge-find.py — recuperación DETERMINISTA de la memoria técnica del proyecto (`docs/knowledge/`).

Sustituye «lee el índice de 3.685 tokens y decide» por «pregunta y recibe» (iniciativa
`memory-retrieval`, `analysis.md` §3 R1). Tres capas, al estilo de las tres herramientas MCP de
`claude-mem` pero sin modelo, sin servicio y sin dependencias (solo stdlib; `sqlite3` incluido):

  1. consulta  → aciertos COMPACTOS, una línea por entrada (~25 tokens), ordenados por relevancia:
                 `ID · estado · área · titular · ruta`   (≤ LINEA_MAX = 120 caracteres, el ESTADO
                 delante: `aceptada` es doctrina, `propuesta` indicio, `obsoleta` basura con sucesor).
  2. --related → grafo CURADO de una entrada (sucesión · misma iniciativa · misma área). NO cronología.
  3. --show    → la entrada completa.

Corpus (fuente de verdad, en git): `<root>/docs/knowledge/{adr,gotchas,lessons}/*.md` más el índice
`docs/knowledge/README.md` — que aporta el `Área` y el titular de los ADR (su frontmatter no los lleva).
`<root>` = `--root` → `$CLAUDE_PROJECT_DIR` → directorio actual.

Área y tipo se casan NORMALIZADOS (minúsculas, sin acentos, por token con prefijo), no por cadena
exacta: `--area estimacion` encuentra «Estimación / calibración» (medido: 21 áreas distintas para 31
entradas, casi todas singleton, con `/` y acentos). `--tipo` admite `adr` · `gotcha(s)`/`got` ·
`lesson(s)`/`leccion(es)`/`les`.

Relevancia (misma función en el camino con índice y en el plano, para que los aciertos sean idénticos):
por cada token de la consulta que casa (prefijo) → +12 en el ID, +6 en el titular, +4 en el área,
+2 en el texto (+1 por aparición extra, tope +4); +5 si todos los tokens casan. Desempate: estado
(aceptada < propuesta < obsoleta), tipo (adr < gotcha < leccion), número. Sin consulta libre, solo el
desempate: doctrina primero, por ID.

Línea compacta: si no cabe en LINEA_MAX se recorta el titular en palabra («…»); si aún no cabe, la
ruta se abrevia a `carpeta/ID-…` (el detalle se abre por ID con `--show`; el JSON siempre trae la
ruta completa); si aún no cabe, se recorta el área. En la salida humana la ruta es relativa a
`docs/knowledge/`; en `--json`, relativa al proyecto (`docs/knowledge/…`).

Salida `--json` de la capa 1 — CONTRATO (la consumen `task-brief.py` y `session-context.sh`; cambiar
una clave rompe dos piezas):
  {"version": 1,
   "indice": "construido" | "reconstruido" | "cache" | "degradado",
   "consulta": {"texto": str, "area": str, "tipo": str, "limit": int},
   "total": int,                          # aciertos ANTES de aplicar --limit
   "aciertos": [ {"id", "tipo", "estado", "estado_detalle", "area", "titular", "ruta", "linea",
                  "puntuacion", "iniciativa", "fecha"} ]}   # en este orden de claves
`indice`: "degradado" = recorrido plano de los ficheros (sin índice); los otros tres valores los
introduce la capa 3 (índice SQLite FTS5 en `.claude/`, T-03). `indice_motivo` (solo con "degradado")
dice por qué. Sin `docs/knowledge/` → `{"aciertos": [], "total": 0, …}` en JSON y NADA en texto.

Uso:
  knowledge-find.py [texto libre…] [--area A] [--tipo T] [--limit N] [--json] [--root DIR]
  knowledge-find.py --related <ID> [--json] [--root DIR]
  knowledge-find.py --show <ID> [--json] [--root DIR]
Exit codes:
  0  consulta atendida (también con 0 aciertos, sin `docs/knowledge/` o con el índice degradado:
     la degradación NUNCA bloquea y NUNCA cambia el exit code);
  1  `--show`/`--related` con un ID que no existe (error de uso: una línea en stderr);
  2  argumentos inválidos (argparse).
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

VERSION_JSON = 1
LINEA_MAX = 120            # ≤ 30 tokens por acierto (spec CA-02)
LIMIT_DEFAULT = 10         # `--limit 0` = sin tope
TITULAR_MIN = 40           # antes de abreviar la ruta, el titular conserva al menos esto (es lo que informa)
TITULAR_MIN_DURO = 12      # con la ruta abreviada, el área cede antes de bajar el titular de aquí
CARPETAS = (("adr", "adr"), ("gotchas", "gotcha"), ("lessons", "leccion"))   # carpeta → tipo
TIPO_DE_PREFIJO = {"ADR": "adr", "GOT": "gotcha", "LES": "leccion"}
TIPO_ORDEN = {"adr": 0, "gotcha": 1, "leccion": 2}
ESTADO_ORDEN = {"aceptada": 0, "propuesta": 1, "obsoleta": 2}
SINONIMOS_TIPO = {
    "adr": "adr", "adrs": "adr",
    "gotcha": "gotcha", "gotchas": "gotcha", "got": "gotcha",
    "lesson": "leccion", "lessons": "leccion", "leccion": "leccion", "lecciones": "leccion", "les": "leccion",
}
ID_RE = re.compile(r"\b(ADR|GOT|LES)-(\d{3})\b")
SEP = " · "

# ------------------------------------------------------------------ normalización

def normaliza(s):
    """Minúsculas, sin acentos (NFKD), espacios plegados."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()


def tokens(s):
    """Tokens alfanuméricos normalizados (misma segmentación que el tokenizador `unicode61` de FTS5)."""
    return re.findall(r"[0-9a-z]+", normaliza(s))


def casa(tok, campo_tokens):
    """¿`tok` es prefijo de algún token del campo? (mismo criterio que `"tok"*` en FTS5)."""
    return any(t.startswith(tok) for t in campo_tokens)


def tipo_normalizado(t):
    return SINONIMOS_TIPO.get(normaliza(t)) if t else None


def estado_corto(estado):
    m = re.match(r"\s*([a-záéíóú-]+)", estado or "", re.I)
    return normaliza(m.group(1)) if m else "?"


# ------------------------------------------------------------------ lectura del corpus

def frontmatter(text):
    """{clave: valor} del frontmatter YAML plano + cuerpo. Nunca lanza; sin frontmatter → ({}, text)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    out, key = {}, None
    for raw in text[3:end].splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] not in " \t" and ":" in raw:
            key, val = raw.split(":", 1)
            key, val = key.strip(), val.split(" #", 1)[0].strip() if not val.strip().startswith("#") else ""
            out[key] = val.strip("\"'")
        elif key and raw[0] in " \t":
            out[key] = (out.get(key, "") + " " + raw.strip()).strip()
    cuerpo = text[end + 4:]
    return out, cuerpo[cuerpo.find("\n") + 1:] if "\n" in cuerpo else ""


def celdas(fila):
    """Celdas de una fila `| a | b |` respetando `|` dentro de acentos graves."""
    out, actual, en_codigo = [], [], False
    for ch in fila.strip():
        if ch == "`":
            en_codigo = not en_codigo
        if ch == "|" and not en_codigo:
            out.append("".join(actual).strip())
            actual = []
        else:
            actual.append(ch)
    out.append("".join(actual).strip())
    if out and out[0] == "":
        out = out[1:]
    if out and out[-1] == "":
        out = out[:-1]
    return out


def parse_indice(texto):
    """Filas de la tabla del índice `docs/knowledge/README.md` → lista de dicts
    {id, ruta_rel (relativa a docs/knowledge), titular_indice, area, estado, fuente, linea}.
    La tabla es el bloque CONTIGUO de líneas `|` desde la cabecera `| Entrada |` (como `tabla_y_cola`)."""
    lineas = texto.split("\n")
    ini = next((i for i, l in enumerate(lineas) if l.startswith("| Entrada |")), None)
    if ini is None:
        return []
    filas = []
    for n in range(ini + 2, len(lineas)):
        l = lineas[n]
        if not l.startswith("|"):
            break
        c = celdas(l)
        if len(c) < 4:
            continue
        entrada = re.sub(r"<!--.*?-->", "", c[0]).strip()
        m = re.search(r"\]\(([^)\s]+)\)", entrada)
        ruta_rel = m.group(1) if m else ""
        titular = ""
        if " — " in entrada:
            titular = entrada.split(" — ", 1)[1].strip()
        filas.append({
            "id": c[1] if len(c) > 1 else "",
            "ruta_rel": ruta_rel,
            "titular_indice": _limpia_titular(titular),
            "area": c[3] if len(c) > 3 else "",
            "estado": c[4] if len(c) > 4 else "",
            "fuente": c[5] if len(c) > 5 else "",
            "linea": n + 1,
        })
    return filas


def _limpia_titular(t):
    t = re.sub(r"<!--.*?-->", "", t or "").strip()
    t = re.sub(r"\s+", " ", t)
    # «"Frase." (1/3)» → «Frase. (1/3)»: las comillas del índice no informan y cuestan caracteres
    m = re.match(r"^[\"“«](.+?)[\"”»](\s*\(.*\))?$", t)
    if m:
        t = (m.group(1).strip() + (m.group(2) or "")).strip()
    return t


def _titular_del_cuerpo(cuerpo):
    for l in cuerpo.split("\n"):
        if l.startswith("#"):
            t = l.lstrip("#").strip()
            return re.sub(r"^(?:ADR|GOT|LES)-\d{3}\s*[:—-]\s*", "", t)
    return ""


_INICIATIVA_RE = re.compile(r"(?:^|[/\s`(])(?:\d{4}-\d{2}-\d{2}-)?([a-z][a-z0-9]*(?:-[a-z0-9]+)+)/(?:spec|tasks|retro|evaluation|improvement-plan|test-plan)\.md")


def iniciativa_de(fm, fila):
    """Slug de la iniciativa (sin fecha): frontmatter `iniciativa`, si no el primer
    `<fecha>-<slug>/{spec,tasks,retro,…}.md` de `fuente` (frontmatter) o de la columna Fuente."""
    ini = (fm.get("iniciativa") or "").strip()
    if ini:
        return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", ini)
    for texto in (fm.get("fuente", ""), (fila or {}).get("fuente", "")):
        m = _INICIATIVA_RE.search(texto or "")
        if m:
            return m.group(1)
    return ""


def _ids_en(texto):
    return [f"{a}-{b}" for a, b in ID_RE.findall(texto or "")]


def leer_entrada(root, carpeta, tipo, fichero, filas_por_ruta):
    ruta_rel = f"{carpeta}/{fichero}"
    path = os.path.join(root, "docs", "knowledge", carpeta, fichero)
    try:
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
    except (OSError, UnicodeDecodeError):
        return None
    fm, cuerpo = frontmatter(text)
    fila = filas_por_ruta.get(ruta_rel, {})
    m = ID_RE.search(fm.get("id", "")) or ID_RE.search(fichero)
    id_ = f"{m.group(1)}-{m.group(2)}" if m else fichero[:-3]
    estado_detalle = (fm.get("estado") or fila.get("estado") or "").strip()
    titular = fila.get("titular_indice") or fm.get("titulo") or _titular_del_cuerpo(cuerpo) or fichero[:-3]
    sucesores = _ids_en(" ".join(fm.get(k, "") for k in ("sucesor", "sustituida_por", "sustituida-por",
                                                             "reemplazada_por", "sucesora")))
    if estado_corto(estado_detalle) == "obsoleta":
        sucesores += [i for i in _ids_en(estado_detalle) if i != id_ and i not in sucesores]
    sustituye = _ids_en(" ".join(fm.get(k, "") for k in ("sustituye", "sustituye_a", "reemplaza", "predecesora")))
    return {
        "id": id_,
        "tipo": tipo,
        "estado": estado_corto(estado_detalle),
        "estado_detalle": estado_detalle,
        "area": (fm.get("area") or fila.get("area") or "").strip(),
        "titular": titular,
        "ruta": f"docs/knowledge/{ruta_rel}",
        "ruta_corta": ruta_rel,
        "iniciativa": iniciativa_de(fm, fila),
        "fecha": (fm.get("fecha") or "").strip(),
        "sucesores": sucesores,
        "sustituye": sustituye,
        "texto": text,
    }


def cargar_corpus(root):
    """Todas las entradas de `<root>/docs/knowledge/{adr,gotchas,lessons}/*.md` (o [] si no hay carpeta),
    en orden fijo (carpeta, nombre)."""
    base = os.path.join(root, "docs", "knowledge")
    if not os.path.isdir(base):
        return []
    filas_por_ruta = {}
    try:
        with open(os.path.join(base, "README.md"), encoding="utf-8-sig") as f:
            for fila in parse_indice(f.read()):
                filas_por_ruta[fila["ruta_rel"]] = fila
    except (OSError, UnicodeDecodeError):
        pass
    out = []
    for carpeta, tipo in CARPETAS:
        d = os.path.join(base, carpeta)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".md") and fn.lower() != "readme.md":
                e = leer_entrada(root, carpeta, tipo, fn, filas_por_ruta)
                if e:
                    out.append(e)
    return out


# ------------------------------------------------------------------ relevancia

def _numero(id_):
    m = re.search(r"(\d+)$", id_)
    return int(m.group(1)) if m else 0


def clave_orden(e):
    return (ESTADO_ORDEN.get(e["estado"], 3), TIPO_ORDEN.get(e["tipo"], 9), _numero(e["id"]), e["id"])


def puntuacion(e, toks):
    """Relevancia de `e` para los tokens de la consulta (0 = no casa). Determinista y explicable."""
    if not toks:
        return 0
    tok_id = tokens(e["id"]) + [normaliza(e["id"])]
    tok_tit = tokens(e["titular"])
    tok_area = tokens(e["area"])
    cnt_texto = Counter(tokens(e["texto"]))
    total, casados = 0, 0
    for t in toks:
        s = 0
        if casa(t, tok_id):
            s += 12
        if casa(t, tok_tit):
            s += 6
        if casa(t, tok_area):
            s += 4
        n = sum(c for tk, c in cnt_texto.items() if tk.startswith(t))
        if n:
            s += 2 + min(n - 1, 4)
        if s:
            casados += 1
        total += s
    if toks and casados == len(toks):
        total += 5
    return total


def filtra_area(e, area_toks):
    return all(casa(t, tokens(e["area"])) for t in area_toks)


def buscar(entradas, texto="", area="", tipo="", limit=LIMIT_DEFAULT):
    """(aciertos ordenados y con `puntuacion`, total antes del limit)."""
    toks = [t for t in dict.fromkeys(tokens(texto)) if len(t) >= 2]
    area_toks = tokens(area)
    tipo_n = tipo_normalizado(tipo) if tipo else None
    out = []
    for e in entradas:
        if tipo and (tipo_n is None or e["tipo"] != tipo_n):
            continue
        if area_toks and not filtra_area(e, area_toks):
            continue
        p = puntuacion(e, toks)
        if toks and p <= 0:
            continue
        out.append(dict(e, puntuacion=p))
    out.sort(key=lambda e: (-e["puntuacion"],) + clave_orden(e))
    total = len(out)
    if limit and limit > 0:
        out = out[:limit]
    return out, total


# ------------------------------------------------------------------ salida

def recorta(s, n):
    """`s` a ≤ n caracteres, en límite de palabra, con «…»."""
    s = re.sub(r"\s+", " ", s or "").strip()
    if len(s) <= n:
        return s
    if n <= 1:
        return "…"[:n]
    corte = s.rfind(" ", 0, n - 1)
    if corte < n // 2:
        corte = n - 1
    return s[:corte].rstrip(",;:—-( ") + "…"


def linea_compacta(e, ancho=LINEA_MAX):
    """`ID · estado · área · titular · ruta` en ≤ `ancho` caracteres (ver docstring del módulo)."""
    id_, estado = e["id"], e["estado"] or "?"
    area = re.sub(r"\s+", " ", e.get("area") or "—").strip()
    titular = re.sub(r"\s+", " ", e.get("titular") or "—").strip()
    ruta = e.get("ruta_corta") or e.get("ruta") or ""
    carpeta = ruta.split("/", 1)[0] if "/" in ruta else ""

    def compone(a, t, r):
        return SEP.join((id_, estado, a, t, r))

    if len(compone(area, titular, ruta)) <= ancho:
        return compone(area, titular, ruta)
    fijo = len(SEP.join((id_, estado, area, "", ruta)))
    if ancho - fijo >= TITULAR_MIN:
        return compone(area, recorta(titular, ancho - fijo), ruta)
    ruta = f"{carpeta}/{id_}-…" if carpeta else f"{id_}-…"
    fijo = len(SEP.join((id_, estado, area, "", ruta)))
    if ancho - fijo >= TITULAR_MIN_DURO:
        return compone(area, recorta(titular, ancho - fijo), ruta)
    base = len(SEP.join((id_, estado, "", "", ruta)))
    area = recorta(area, max(6, ancho - base - TITULAR_MIN_DURO))
    fijo = len(SEP.join((id_, estado, area, "", ruta)))
    return compone(area, recorta(titular, max(1, ancho - fijo)), ruta)[:ancho]


def acierto_json(e):
    return {
        "id": e["id"], "tipo": e["tipo"], "estado": e["estado"], "estado_detalle": e["estado_detalle"],
        "area": e["area"], "titular": e["titular"], "ruta": e["ruta"], "linea": linea_compacta(e),
        "puntuacion": e.get("puntuacion", 0), "iniciativa": e["iniciativa"], "fecha": e["fecha"],
    }


def resolver_root(arg_root):
    if arg_root:
        return os.path.abspath(arg_root)
    env = os.environ.get("CLAUDE_PROJECT_DIR", "")
    return os.path.abspath(env) if env else os.getcwd()


# ------------------------------------------------------------------ CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="recuperación determinista de docs/knowledge/ (tres capas)")
    ap.add_argument("texto", nargs="*", help="consulta libre (capa 1)")
    ap.add_argument("--area", default="", help="área normalizada (minúsculas, sin acentos, por token)")
    ap.add_argument("--tipo", default="", help="adr | gotcha | lesson (y sinónimos)")
    ap.add_argument("--limit", type=int, default=LIMIT_DEFAULT, help=f"aciertos máximos (default {LIMIT_DEFAULT}; 0 = sin tope)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", help="raíz del proyecto (default: $CLAUDE_PROJECT_DIR → cwd)")
    args = ap.parse_args(argv)
    root = resolver_root(args.root)
    texto = " ".join(args.texto)
    entradas = cargar_corpus(root)
    indice = {"indice": "degradado", "indice_motivo": "recorrido plano"}
    aciertos, total = buscar(entradas, texto=texto, area=args.area, tipo=args.tipo, limit=args.limit)
    if args.json:
        data = {"version": VERSION_JSON, "indice": indice["indice"],
                "consulta": {"texto": texto, "area": args.area, "tipo": args.tipo, "limit": args.limit},
                "total": total, "aciertos": [acierto_json(a) for a in aciertos]}
        if indice.get("indice_motivo"):
            data["indice_motivo"] = indice["indice_motivo"]
        print(json.dumps(data, ensure_ascii=False))
    else:
        for a in aciertos:
            print(linea_compacta(a))
    return 0


if __name__ == "__main__":
    sys.exit(main())
