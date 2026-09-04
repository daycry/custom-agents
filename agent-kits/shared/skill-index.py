#!/usr/bin/env python3
"""
skill-index.py — índice COMPACTO y DETERMINISTA de las piezas del plugin (comandos, skills,
agentes) para inyectarlo como contexto al arrancar la sesión (patrón `using-superpowers`).
Cierra la brecha de fiabilidad de activación: la `description` de una skill solo se ve cuando
Claude la busca; este índice pone TODAS las piezas y las reglas de enrutado delante en cada
arranque (`hooks/session-context.sh`, SessionStart `startup|resume|compact`) a coste fijo y
medido: ≤ LIMITE_LINEAS líneas · ≤ LIMITE_CHARS caracteres · ≤ LIMITE_LINEA por línea (los tests
lo afirman). Si hay más piezas de las que caben, cada grupo cede proporcionalmente y cierra con
«… y N piezas más (ver `skills/`)»; si el total de caracteres excede, el ancho por línea baja.

Lee SOLO los frontmatters (nunca los cuerpos): `commands/*.md` (description + argument-hint),
`skills/*/SKILL.md` (name + description) y `agents/*.md` (name + description). Resumen por pieza =
la description recortada en la PRIMERA FRASE o en «Úsalo/Úsala cuando» (lo que llegue antes) y,
si aún excede, cortada en palabra + «…». Una pieza nueva aparece sola: NO se edita a mano.

Caché: `${CLAUDE_PROJECT_DIR}/.claude/.skill-index.cache` (1.ª línea `# skill-index <hash>`,
hash sha256[:16] de los frontmatters + versión del formato). Se regenera solo si el hash cambia
o con `--no-cache`. Sin `CLAUDE_PROJECT_DIR` se usa `$PWD` solo si ya tiene `.claude/`.

Localización del plugin: `--root` → `CLAUDE_PLUGIN_ROOT` → padre de `agent-kits/shared` (este
script) → `find` sobre `$PWD/.claude` y `$HOME/.claude` (regla 5 de CONVENTIONS).

Desactivable por el consumidor: `.claude/dev.json` → `{"sesion": {"indice": false}}` → sin salida.

Uso:
  skill-index.py [--root DIR] [--no-cache] [--cache FICHERO] [--json]
Exit 0 SIEMPRE (la información nunca bloquea): sin piezas / desactivado / error → sin salida.
"""
import argparse
import hashlib
import json
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "2"                      # entra en el hash: cambiar el formato invalida la caché
LIMITE_LINEAS = 45
LIMITE_CHARS = 3500
LIMITE_LINEA = 110
MIN_FRASE = 40                     # una primera frase más corta arrastra la siguiente
CACHE_NOMBRE = ".skill-index.cache"
CABECERA = [
    "Plugin custom-agents — índice de piezas. Antes de cualquier tarea comprueba si aplica una de estas piezas.",
    "Si el usuario describe algo que casa con una skill, invócala (herramienta Skill) en vez de improvisar.",
    "Los comandos se invocan por `/` o por descripción, como las skills; los agentes se delegan por nombre (Agent).",
]
GRUPOS = (("command", "Comandos:"), ("skill", "Skills:"), ("agent", "Agentes:"))
_GATILLO_RE = re.compile(r"\b(Úsal[oa]|Usal[oa]|Use (?:this |it )?when|Invócal[oa])\b", re.I)


# ------------------------------------------------------------------ frontmatter

def frontmatter(path):
    """Parser mínimo: {clave: valor} de nivel 0, con bloques `>`/`|` y continuaciones plegadas.
    Devuelve ({}, "") si el fichero no se puede leer o el frontmatter está roto (nunca lanza)."""
    try:
        text = open(path, encoding="utf-8-sig").read()
    except (OSError, UnicodeDecodeError):
        return {}, ""
    if not text.startswith("---"):
        return {}, ""
    end = text.find("\n---", 3)
    if end == -1:
        return {}, ""
    fm = text[3:end]
    out, key = {}, None
    for raw in fm.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] not in " \t" and ":" in raw:
            key, val = raw.split(":", 1)
            key, val = key.strip(), val.strip()
            out[key] = "" if val in (">", "|", ">-", "|-") else val
        elif key and raw[0] in " \t":
            out[key] = (out.get(key, "") + " " + raw.strip()).strip()
    return out, fm


def piezas(root):
    """[(kind, nombre, description, argument_hint, frontmatter_bruto)] en orden fijo:
    commands, skills, agents — alfabético dentro de cada grupo."""
    out = []
    cmd = os.path.join(root, "commands")
    if os.path.isdir(cmd):
        for fn in sorted(os.listdir(cmd)):
            if fn.endswith(".md"):
                fm, raw = frontmatter(os.path.join(cmd, fn))
                out.append(("command", fn[:-3], fm.get("description", ""), fm.get("argument-hint", ""), raw))
    sk = os.path.join(root, "skills")
    if os.path.isdir(sk):
        for d in sorted(os.listdir(sk)):
            p = os.path.join(sk, d, "SKILL.md")
            if os.path.isfile(p):
                fm, raw = frontmatter(p)
                out.append(("skill", fm.get("name") or d, fm.get("description", ""), "", raw))
    ag = os.path.join(root, "agents")
    if os.path.isdir(ag):
        for fn in sorted(os.listdir(ag)):
            if fn.endswith(".md"):
                fm, raw = frontmatter(os.path.join(ag, fn))
                out.append(("agent", fm.get("name") or fn[:-3], fm.get("description", ""), "", raw))
    return out


def es_plugin(root):
    return bool(root) and any(os.path.isdir(os.path.join(root, d)) for d in ("commands", "skills", "agents"))


def localizar_root():
    """`CLAUDE_PLUGIN_ROOT` → padre de agent-kits/shared → find en $PWD/.claude y $HOME/.claude."""
    env = os.environ.get("CLAUDE_PLUGIN_ROOT", "")
    if es_plugin(env):
        return os.path.abspath(env)
    propio = os.path.dirname(os.path.dirname(HERE))
    if es_plugin(propio):
        return propio
    for base in (os.path.join(os.getcwd(), ".claude"), os.path.join(os.path.expanduser("~"), ".claude")):
        if not os.path.isdir(base):
            continue
        for dirpath, dirnames, _files in os.walk(base):
            if dirpath.endswith(os.sep + os.path.join("agent-kits", "shared")):
                cand = os.path.dirname(os.path.dirname(dirpath))
                if es_plugin(cand):
                    return cand
            dirnames[:] = [d for d in dirnames if d not in ("node_modules", ".git", "__pycache__")]
    return None


# ------------------------------------------------------------------ resumen

def limpiar(desc):
    d = re.sub(r"[`*_]", "", desc or "")
    return re.sub(r"\s+", " ", d).strip()


def primera_frase(d, minimo=MIN_FRASE):
    """Corta en «Úsalo/Úsala cuando» o en la primera frase (`. ` seguido de mayúscula/apertura) que
    reúna ≥ `minimo` caracteres (una primera frase-título muy corta arrastra la siguiente), lo que
    llegue antes; conserva las abreviaturas típicas (p. ej., etc.)."""
    corte = len(d)
    m = _GATILLO_RE.search(d)
    if m and m.start() > 0:
        corte = min(corte, m.start())
    for mm in re.finditer(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡(«\"])", d):
        prev = d[:mm.start()]
        if re.search(r"\b(p\.\s?ej|etc|vs|aprox|núm|máx|mín)\.$", prev, re.I):
            continue
        if mm.start() < minimo:
            continue
        corte = min(corte, mm.start())
        break
    return d[:corte].strip().rstrip(".;:,— -")


def resumen(desc, ancho):
    """Primera frase de la description, recortada a `ancho` caracteres en límite de palabra + «…»."""
    d = limpiar(desc)
    if not d:
        return "(sin description)"
    frase = primera_frase(d) or d
    if len(frase) <= ancho:
        return frase
    corte = frase.rfind(" ", 0, max(1, ancho - 1))
    if corte < ancho // 2:
        corte = ancho - 1
    return frase[:corte].rstrip(",;:—-( ") + "…"


def hint_corto(hint):
    """`argument-hint` compacto: solo los tokens `<…>`/`[…]` (`<objetivo> [rapido | completo]`); sin
    tokens, `(sin argumentos)` → nada, `(opcional) …` → `[opcional]`, otra prosa → `<args>`."""
    h = limpiar(hint).strip("\"'")
    if not h:
        return ""
    toks = re.findall(r"<[^<>]*>|\[[^\[\]]*\]", h)
    if toks:
        return " ".join(toks)
    if h.lower().startswith("(sin argumentos)"):
        return ""
    if h.lower().startswith("(opcional)"):
        return "[opcional]"
    return "<args>"


def hash_frontmatters(ps):
    h = hashlib.sha256(f"v{VERSION}\n".encode("utf-8"))
    for kind, nombre, _desc, _hint, raw in ps:
        h.update(f"{kind}:{nombre}\n{raw}\n\0".encode("utf-8"))
    return h.hexdigest()[:16]


CARPETA = {"command": "commands/", "skill": "skills/", "agent": "agents/"}


def _cupos(ps):
    """Piezas por grupo que caben en LIMITE_LINEAS: si sobran, cada grupo cede proporcionalmente
    (floor) y la última línea del grupo recortado pasa a ser «… y N piezas más»."""
    n = {k: sum(1 for p in ps if p[0] == k) for k, _t in GRUPOS}
    grupos = sum(1 for k in n if n[k])
    presupuesto = LIMITE_LINEAS - len(CABECERA) - grupos
    total = sum(n.values())
    if total <= presupuesto:
        return n
    cupo = {}
    for k in n:
        if not n[k]:
            cupo[k] = 0
            continue
        # cada grupo recortado gasta una línea en «… y N más»; el resto proporcional
        c = max(1, (presupuesto * n[k]) // total)
        cupo[k] = n[k] if c >= n[k] else max(1, c - 1)
    # ajuste determinista: si aún sobra, quita del grupo mayor; si falta, no se añade nada
    while sum(cupo[k] + (1 if cupo[k] < n[k] else 0) for k in cupo) > presupuesto:
        k = max(cupo, key=lambda x: (cupo[x], x))
        if cupo[k] <= 1:
            break
        cupo[k] -= 1
    return cupo


def _lineas(ps, ancho):
    lineas = list(CABECERA)
    cupos = _cupos(ps)
    for kind, titulo in GRUPOS:
        items = [p for p in ps if p[0] == kind]
        if not items:
            continue
        lineas.append(titulo)
        visibles = items[:cupos[kind]]
        if len(visibles) < len(items):
            lineas_extra = [f"… y {len(items) - len(visibles)} piezas más (ver `{CARPETA[kind]}`)"]
        else:
            lineas_extra = []
        for _k, nombre, desc, hint, _raw in visibles:
            etiqueta = f"/{nombre}" if kind == "command" else nombre
            h = hint_corto(hint)
            if h:
                tope = ancho // 2 - len(etiqueta) - 1        # el hint no roba más de media línea
                if len(h) > tope:
                    c = h.rfind(" ", 0, max(1, tope - 1))
                    h = h[:c if c >= tope // 2 else tope - 1].rstrip(",;:( ") + "…"
                etiqueta = f"{etiqueta} {h}"
            libre = ancho - len(etiqueta) - 3            # « — »
            lineas.append(f"{etiqueta} — {resumen(desc, max(20, libre))}")
        lineas.extend(lineas_extra)
    return lineas


def construir(ps):
    """Índice dentro de los topes: si con LIMITE_LINEA por línea el total excede LIMITE_CHARS, el
    ancho por línea baja de 5 en 5 (determinista) hasta caber. Devuelve None sin piezas."""
    if not ps:
        return None
    ancho = LIMITE_LINEA
    while True:
        lineas = _lineas(ps, ancho)
        texto = "\n".join(lineas)
        if len(texto) <= LIMITE_CHARS or ancho <= 40:
            break
        ancho -= 5
    return {"lineas": lineas, "texto": texto, "chars": len(texto), "n_lineas": len(lineas),
            "ancho": ancho, "hash": hash_frontmatters(ps), "piezas": len(ps)}


# ------------------------------------------------------------------ config + caché

def proyecto_dir():
    """Raíz del proyecto consumidor: CLAUDE_PROJECT_DIR; si no, $PWD solo si ya tiene `.claude/`."""
    env = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if env:
        return os.path.abspath(env)
    if os.path.isdir(os.path.join(os.getcwd(), ".claude")):
        return os.getcwd()
    return None


def indice_desactivado(proj):
    """`.claude/dev.json` → sesion.indice == false. Fichero ausente/corrupto → activado."""
    if not proj:
        return False
    try:
        with open(os.path.join(proj, ".claude", "dev.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        sesion = cfg.get("sesion") if isinstance(cfg, dict) else None
        return isinstance(sesion, dict) and sesion.get("indice") is False
    except (OSError, ValueError, AttributeError):
        return False


def leer_cache(path):
    """(hash, texto) de la caché o (None, None)."""
    try:
        with open(path, encoding="utf-8") as f:
            primera = f.readline()
            resto = f.read()
    except (OSError, UnicodeDecodeError, ValueError):
        return None, None          # caché ilegible/corrupta → se regenera y se sobrescribe
    m = re.match(r"# skill-index ([0-9a-f]{16})\n?$", primera)
    return (m.group(1), resto.rstrip("\n")) if m else (None, None)


def escribir_cache(path, idx):
    tmp = f"{path}.{os.getpid()}.tmp"
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(f"# skill-index {idx['hash']}\n{idx['texto']}\n")
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def generar(root, cache=None, usar_cache=True):
    """Texto del índice (o None). Usa/renueva la caché si `cache` es una ruta y `usar_cache`."""
    ps = piezas(root)
    if not ps:
        return None
    h = hash_frontmatters(ps)
    if cache and usar_cache:
        h_cache, texto_cache = leer_cache(cache)
        if h_cache == h and texto_cache:
            return {"texto": texto_cache, "hash": h, "cache": True, "piezas": len(ps),
                    "chars": len(texto_cache), "n_lineas": texto_cache.count("\n") + 1,
                    "lineas": texto_cache.split("\n")}
    idx = construir(ps)
    idx["cache"] = False
    if cache and usar_cache:
        escribir_cache(cache, idx)
    return idx


def main(argv=None):
    ap = argparse.ArgumentParser(description="índice compacto de comandos/skills/agentes del plugin")
    ap.add_argument("--root", help="raíz del plugin (default: CLAUDE_PLUGIN_ROOT → este kit → find)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-cache", action="store_true", help="ignora y no escribe la caché")
    ap.add_argument("--cache", metavar="FICHERO", help=f"ruta de la caché (default: <proyecto>/.claude/{CACHE_NOMBRE})")
    args = ap.parse_args(argv)

    try:
        proj = proyecto_dir()
        if indice_desactivado(proj):
            return 0
        root = os.path.abspath(args.root) if args.root else localizar_root()
        if not root or not es_plugin(root):
            return 0
        cache = args.cache or (os.path.join(proj, ".claude", CACHE_NOMBRE) if proj else None)
        idx = generar(root, cache=cache, usar_cache=not args.no_cache)
        if not idx:
            return 0
        if args.json:
            print(json.dumps(idx, ensure_ascii=False))
        else:
            print(idx["texto"])
    except Exception as e:  # noqa: BLE001 — la información nunca bloquea
        print(f"skill-index: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
