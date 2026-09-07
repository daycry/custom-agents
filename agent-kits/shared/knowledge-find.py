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
`indice_motivo` (solo con "degradado") dice por qué. Sin `docs/knowledge/` → `{"aciertos": [],
"total": 0, "indice": "degradado", …}` en JSON y NADA en texto.

Índice (capa 3, caché — NO es el almacén): SQLite con FTS5 en `<root>/.claude/knowledge-index.sqlite`
(en `.gitignore`), reconstruible desde los ficheros. Guarda el hash sha256 del CONTENIDO del corpus
(README + cada entrada, en bytes: tocar el mtime no invalida; cambiar una letra sí) y las entradas
ya parseadas más una tabla FTS5 (`unicode61 remove_diacritics 2`, la misma segmentación que
`tokens()`). Estados que informa `indice`:
  "construido"   no existía → se crea y se responde;
  "reconstruido" existía corrupto, o su hash no cuadra → se regenera (tmp + os.replace, atómico);
  "cache"        hash idéntico → se usan las entradas y la FTS del índice sin parsear los ficheros;
  "degradado"    no se puede usar ni escribir (`.claude/` no escribible, `sqlite3` sin FTS5, `--no-index`,
                 sin corpus) → RECORRIDO PLANO de los ficheros con LOS MISMOS aciertos (misma función de
                 relevancia; FTS5 solo preselecciona candidatos con `MATCH "tok"*`).
El índice NUNCA cambia el exit code: cualquier error suyo cae al recorrido plano.

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
import hashlib
import json
import os
import re
import sqlite3
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
RELATED_TOPE_CHARS = 1600      # capa 2 ≤ 400 tokens (spec CA-03); si no cabe, se recorta y se dice
RELATED_MAX_POR_GRUPO = 6      # entradas por grupo antes de «… y N más»
AREA_TOKEN_MIN = 4             # tokens del área que cuentan como «misma área» (fuera: de, del, y, por…)
AREA_STOPWORDS = {"para", "como", "sobre", "entre", "desde", "hacia", "cada"}
INDICE_NOMBRE = "knowledge-index.sqlite"   # en <root>/.claude/ (+ .gitignore)
INDICE_VERSION = "1"                        # entra en el hash: cambiar el esquema invalida el índice
CAMPOS = ("id", "tipo", "estado", "estado_detalle", "area", "titular", "ruta", "ruta_corta", "iniciativa",
          "fecha", "sucesores", "sustituye", "texto")

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


def leer_entrada(carpeta, tipo, fichero, text, filas_por_ruta):
    ruta_rel = f"{carpeta}/{fichero}"
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


def ficheros_corpus(root):
    """[(ruta relativa a docs/knowledge, bytes)] del corpus en orden fijo: README.md primero y luego
    `adr/`, `gotchas/`, `lessons/` por nombre. [] si no hay `docs/knowledge/`. Ficheros ilegibles se saltan."""
    base = os.path.join(root, "docs", "knowledge")
    if not os.path.isdir(base):
        return []
    out = []
    readme = os.path.join(base, "README.md")
    if os.path.isfile(readme):
        try:
            with open(readme, "rb") as f:
                out.append(("README.md", f.read()))
        except OSError:
            pass
    for carpeta, _tipo in CARPETAS:
        d = os.path.join(base, carpeta)
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if fn.endswith(".md") and fn.lower() != "readme.md":
                try:
                    with open(os.path.join(d, fn), "rb") as f:
                        out.append((f"{carpeta}/{fn}", f.read()))
                except OSError:
                    continue
    return out


def hash_corpus(ficheros):
    h = hashlib.sha256(f"knowledge-index v{INDICE_VERSION}\n".encode("utf-8"))
    for rel, data in ficheros:
        h.update(rel.encode("utf-8") + b"\0" + data + b"\0")
    return h.hexdigest()


def _texto(data):
    return data.decode("utf-8-sig", "replace")


def parsear_corpus(ficheros):
    """Entradas parseadas a partir de `ficheros_corpus()` (el README aporta área/titular a las filas)."""
    filas_por_ruta = {}
    tipo_de = dict(CARPETAS)
    for rel, data in ficheros:
        if rel == "README.md":
            for fila in parse_indice(_texto(data)):
                filas_por_ruta[fila["ruta_rel"]] = fila
    out = []
    for rel, data in ficheros:
        if rel == "README.md" or "/" not in rel:
            continue
        carpeta, fn = rel.split("/", 1)
        out.append(leer_entrada(carpeta, tipo_de[carpeta], fn, _texto(data), filas_por_ruta))
    return out


def cargar_corpus(root):
    """Todas las entradas de `<root>/docs/knowledge/{adr,gotchas,lessons}/*.md` (o [] si no hay carpeta),
    leídas del disco (recorrido plano, sin índice)."""
    return parsear_corpus(ficheros_corpus(root))


# ------------------------------------------------------------------ índice SQLite FTS5 (caché reconstruible)

def fts5_disponible():
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE t USING fts5(x)")
        con.close()
        return True
    except sqlite3.Error:
        return False


def ruta_indice(root):
    return os.path.join(root, ".claude", INDICE_NOMBRE)


def _fila_a_entrada(row):
    e = dict(zip(CAMPOS, row))
    e["sucesores"] = json.loads(e["sucesores"] or "[]")
    e["sustituye"] = json.loads(e["sustituye"] or "[]")
    return e


def leer_indice(path, h):
    """Entradas del índice si existe, abre, y su hash coincide con `h`; si no, None (y por qué)."""
    if not os.path.isfile(path):
        return None, "construido"
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            row = con.execute("SELECT valor FROM meta WHERE clave = 'hash'").fetchone()
            if not row or row[0] != h:
                return None, "reconstruido"
            filas = con.execute(f"SELECT {', '.join(CAMPOS)} FROM entradas ORDER BY orden").fetchall()
            return [_fila_a_entrada(r) for r in filas], "cache"
        finally:
            con.close()
    except sqlite3.Error:
        return None, "reconstruido"          # bytes basura, esquema viejo, fichero a medias…


def construir_indice(path, entradas, h):
    """Escribe el índice ENTERO en un temporal y lo mueve encima (atómico). Lanza OSError/sqlite3.Error."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = f"{path}.{os.getpid()}.tmp"
    try:
        con = sqlite3.connect(tmp)
        try:
            con.executescript(
                "CREATE TABLE meta(clave TEXT PRIMARY KEY, valor TEXT);"
                "CREATE TABLE entradas(orden INTEGER PRIMARY KEY, " + ", ".join(f"{c} TEXT" for c in CAMPOS) + ");"
                "CREATE VIRTUAL TABLE fts USING fts5(id, titular, area, texto, tokenize='unicode61 remove_diacritics 2');")
            con.executemany("INSERT INTO meta VALUES (?, ?)", [("hash", h), ("version", INDICE_VERSION)])
            con.executemany(
                f"INSERT INTO entradas(orden, {', '.join(CAMPOS)}) VALUES ({', '.join('?' * (len(CAMPOS) + 1))})",
                [(n,) + tuple(json.dumps(e[c], ensure_ascii=False) if c in ("sucesores", "sustituye") else e[c]
                              for c in CAMPOS) for n, e in enumerate(entradas)])
            con.executemany("INSERT INTO fts(id, titular, area, texto) VALUES (?, ?, ?, ?)",
                            [(e["id"], e["titular"], e["area"], e["texto"]) for e in entradas])
            con.commit()
        finally:
            con.close()
        os.replace(tmp, path)
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def abrir_corpus(root, usar_indice=True):
    """(entradas, ruta_del_indice_o_None, {"indice": …[, "indice_motivo": …]}). Nunca lanza."""
    ficheros = ficheros_corpus(root)
    if not ficheros:
        return [], None, {"indice": "degradado", "indice_motivo": "sin docs/knowledge/"}
    if not usar_indice:
        return parsear_corpus(ficheros), None, {"indice": "degradado", "indice_motivo": "--no-index"}
    try:
        if not fts5_disponible():
            return parsear_corpus(ficheros), None, {"indice": "degradado", "indice_motivo": "sqlite3 sin FTS5"}
        path = ruta_indice(root)
        h = hash_corpus(ficheros)
        entradas, estado = leer_indice(path, h)
        if entradas is not None:
            return entradas, path, {"indice": estado}
        entradas = parsear_corpus(ficheros)
        construir_indice(path, entradas, h)
        return entradas, path, {"indice": estado}
    except Exception as e:  # noqa: BLE001 — el índice nunca bloquea ni cambia el exit code
        return parsear_corpus(ficheros), None, {"indice": "degradado", "indice_motivo": f"{type(e).__name__}: {e}"}


def candidatos_fts(path, toks):
    """IDs que casan en la FTS con `"tok"* OR …` (preselección), o None = todos (sin tokens o error)."""
    if not path or not toks:
        return None
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            q = " OR ".join(f'"{t}"*' for t in toks)
            return {r[0] for r in con.execute("SELECT id FROM fts WHERE fts MATCH ?", (q,))}
        finally:
            con.close()
    except sqlite3.Error:
        return None


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


def tokens_consulta(texto):
    return [t for t in dict.fromkeys(tokens(texto)) if len(t) >= 2]


def buscar(entradas, texto="", area="", tipo="", limit=LIMIT_DEFAULT, candidatos=None):
    """(aciertos ordenados y con `puntuacion`, total antes del limit). `candidatos` (IDs de la FTS)
    solo PRESELECCIONA: la relevancia y el filtro `puntuacion > 0` son los mismos con y sin índice."""
    toks = tokens_consulta(texto)
    area_toks = tokens(area)
    tipo_n = tipo_normalizado(tipo) if tipo else None
    out = []
    for e in entradas:
        if candidatos is not None and toks and e["id"] not in candidatos:
            continue
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


# ------------------------------------------------------------------ capa 2: grafo curado

def buscar_id(entradas, id_):
    id_n = (id_ or "").strip().upper()
    return next((e for e in entradas if e["id"].upper() == id_n), None)


def _area_significativa(area):
    return {t for t in tokens(area) if len(t) >= AREA_TOKEN_MIN and t not in AREA_STOPWORDS}


def relaciones(entradas, e):
    """Las tres relaciones CURADAS de `e` (nunca cronología):
      sucesion   → [(relacion, entrada|None, id)]: `sustituida por` (sucesores declarados en `e` o en
                   el `estado` de una obsoleta, o quien declara `sustituye: e`) y `sustituye a` (lo que
                   `e` declara sustituir, o quien declara a `e` como su `sucesor`). `entrada` es None
                   si el ID no está en el corpus.
      iniciativa → entradas con la misma `iniciativa` (frontmatter o deducida de la fuente), sin `e`.
      area       → entradas cuya área comparte ≥ 1 token significativo con la de `e`, por número de
                   tokens compartidos y luego doctrina primero / por ID, sin `e`.
    """
    por_id = {x["id"]: x for x in entradas}
    suc, vistos = [], set()

    def add(rel, id_):
        if (rel, id_) in vistos or id_ == e["id"]:
            return
        vistos.add((rel, id_))
        suc.append((rel, por_id.get(id_), id_))

    for id_ in e["sucesores"]:
        add("sustituida por", id_)
    for id_ in e["sustituye"]:
        add("sustituye a", id_)
    for x in entradas:
        if e["id"] in x["sustituye"]:
            add("sustituida por", x["id"])
        if e["id"] in x["sucesores"]:
            add("sustituye a", x["id"])
    suc.sort(key=lambda t: (0 if t[0] == "sustituida por" else 1, _numero(t[2]), t[2]))

    ini = [x for x in entradas if e["iniciativa"] and x["iniciativa"] == e["iniciativa"] and x["id"] != e["id"]]
    ini.sort(key=clave_orden)

    mios = _area_significativa(e["area"])
    area = []
    for x in entradas:
        if x["id"] == e["id"] or not mios:
            continue
        comunes = len(mios & _area_significativa(x["area"]))
        if comunes:
            area.append((comunes, x))
    area.sort(key=lambda t: (-t[0],) + clave_orden(t[1]))
    return {"sucesion": suc, "iniciativa": ini, "area": [x for _c, x in area]}


def _linea_sucesion(rel, x, id_):
    prefijo = f"{rel} → "
    if x is None:
        return f"{prefijo}{id_} (no está en el corpus)"
    return prefijo + linea_compacta(x, LINEA_MAX - len(prefijo))


def texto_related(e, rel):
    """Salida humana de la capa 2, topada a RELATED_TOPE_CHARS: tres grupos etiquetados y separados;
    un grupo vacío dice `(ninguna)`; si el conjunto no cabe, los grupos ceden entradas desde el más
    largo y lo declaran con «… y N más»."""
    grupos = [
        ("Sucesión:", [_linea_sucesion(r, x, i) for r, x, i in rel["sucesion"]], None),
        (f"Misma iniciativa ({e['iniciativa']}):" if e["iniciativa"] else "Misma iniciativa (sin iniciativa conocida):",
         [linea_compacta(x) for x in rel["iniciativa"]], None),
        (f"Misma área ({e['area']}):" if e["area"] else "Misma área (sin área):",
         [linea_compacta(x) for x in rel["area"]], e["area"]),
    ]
    visibles = [min(len(ls), RELATED_MAX_POR_GRUPO) for _t, ls, _a in grupos]

    def render():
        out = [linea_compacta(e)]
        for (titulo, lineas, area), n in zip(grupos, visibles):
            out.append(titulo)
            if not lineas:
                out.append("(ninguna)")
                continue
            out.extend(lineas[:n])
            if n < len(lineas):
                pista = f" (`--area \"{area}\"` las lista todas)" if area else ""
                out.append(f"… y {len(lineas) - n} más{pista}")
        return "\n".join(out) + "\n"

    texto = render()
    while len(texto) > RELATED_TOPE_CHARS and any(n > 1 for n in visibles):
        k = max(range(len(grupos)), key=lambda i: (visibles[i], i))
        visibles[k] -= 1
        texto = render()
    return texto


def json_related(e, rel, indice):
    data = {"version": VERSION_JSON, "indice": indice["indice"], "entrada": acierto_json(e), "relaciones": {
        "sucesion": [dict(relacion=r, **(acierto_json(x) if x else {"id": i, "ausente": True}))
                     for r, x, i in rel["sucesion"]],
        "iniciativa": {"clave": e["iniciativa"], "aciertos": [acierto_json(x) for x in rel["iniciativa"]]},
        "area": {"clave": e["area"], "aciertos": [acierto_json(x) for x in rel["area"]]},
    }}
    if indice.get("indice_motivo"):
        data["indice_motivo"] = indice["indice_motivo"]
    return data


# ------------------------------------------------------------------ CLI

def main(argv=None):
    ap = argparse.ArgumentParser(description="recuperación determinista de docs/knowledge/ (tres capas)")
    ap.add_argument("texto", nargs="*", help="consulta libre (capa 1)")
    ap.add_argument("--area", default="", help="área normalizada (minúsculas, sin acentos, por token)")
    ap.add_argument("--tipo", default="", help="adr | gotcha | lesson (y sinónimos)")
    ap.add_argument("--limit", type=int, default=LIMIT_DEFAULT, help=f"aciertos máximos (default {LIMIT_DEFAULT}; 0 = sin tope)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", help="raíz del proyecto (default: $CLAUDE_PROJECT_DIR → cwd)")
    ap.add_argument("--no-index", action="store_true", help="recorrido plano de los ficheros, sin leer ni escribir el índice")
    capa = ap.add_mutually_exclusive_group()
    capa.add_argument("--related", metavar="ID", help="capa 2: grafo curado de una entrada")
    capa.add_argument("--show", metavar="ID", help="capa 3: la entrada completa")
    args = ap.parse_args(argv)
    root = resolver_root(args.root)
    texto = " ".join(args.texto)
    entradas, path, indice = abrir_corpus(root, usar_indice=not args.no_index)

    if args.related or args.show:
        id_ = args.related or args.show
        e = buscar_id(entradas, id_)
        if e is None:
            print(f"knowledge-find: no hay ninguna entrada con ID `{id_}` en {os.path.join(root, 'docs', 'knowledge')}",
                  file=sys.stderr)
            return 1
        if args.show:
            if args.json:
                data = {"version": VERSION_JSON, "indice": indice["indice"], "id": e["id"], "tipo": e["tipo"],
                        "estado": e["estado"], "estado_detalle": e["estado_detalle"], "area": e["area"],
                        "titular": e["titular"], "ruta": e["ruta"], "contenido": e["texto"]}
                if indice.get("indice_motivo"):
                    data["indice_motivo"] = indice["indice_motivo"]
                print(json.dumps(data, ensure_ascii=False))
            else:
                sys.stdout.write(e["texto"])
            return 0
        rel = relaciones(entradas, e)
        if args.json:
            print(json.dumps(json_related(e, rel, indice), ensure_ascii=False))
        else:
            sys.stdout.write(texto_related(e, rel))
        return 0

    candidatos = candidatos_fts(path, tokens_consulta(texto))
    aciertos, total = buscar(entradas, texto=texto, area=args.area, tipo=args.tipo, limit=args.limit,
                             candidatos=candidatos)
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
