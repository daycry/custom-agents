#!/usr/bin/env python3
"""
review-lens-select.py — decide de forma DETERMINISTA si la Lente C (seguridad) de la skill
`adversarial-review` aplica a un diff.

(Iniciativa adversarial-review: la revisión de dos lentes A+B se lanza siempre; la lente C solo
si el diff toca algo sensible — así no se gasta un tercer revisor en cambios de prosa o de
scripts inocuos. La decisión va en script con tests, no en el juicio del orquestador.)

Qué hace:
  1. Ficheros cambiados = `git diff --name-only <base>` (base…working tree: comiteado + sin
     comitear) ∪ untracked (`git status --porcelain`), o los `--files` dados (sin git).
     base: `--base <ref>`; si no, merge-base con `main`/`master`; si la rama actual ES la
     principal → HEAD (solo cambios sin comitear); si no hay base clara → aviso y HEAD.
  2. Heurística por RUTA (case-insensitive), con los stems ANCLADOS al inicio de un token de la
     ruta (`(?<![a-z0-9])`: `authz.py`, `session-context.sh`, `jwt_utils.py` sí; `oracle.py`,
     `myacl.py` no) y, en los stems que son también prefijo de palabras inocuas, con LÍMITE final
     (`(?![a-z])`: `tokens.py`/`token_store.py` sí, `tokenizer.py` no; `helm/` sí, `helmet.py` no;
     `acl.py` sí, `aclimate.py` no; `auth(?!or)`: `auth_middleware.py` sí, `author.md` no). Lista
     exacta = RUTA_RE (abajo): auth|login|session(s)|token(s)|oauth|jwt|password|passwd|secret(s)|
     crypt|permission(s)|acl|rbac|cors|csrf|upload|payment|billing|docker|nginx|k8s|helm; y como
     casos aparte `.env*`, `Dockerfile*` y `.github/workflows/`. La ruta NO se evalúa para prosa
     (.md/.txt/.rst) ni para `docs/**` (`docs/author.md`, `docs/roadmap/…-token-diet/` no son
     superficie de ataque); `tests/**` sí se evalúa por ruta. `.claude/dev.json` →
     "revision": {"excluir": ["hooks/**", …]} excluye globs (`**` = cero o más directorios, `*` =
     un nivel; traductor de `confluence-scope.py`) SOLO de la heurística de ruta: un fichero
     excluido sigue escaneándose por CONTENIDO (una línea con ejecución dinámica añadida en `hooks/x.sh` dispara).
  3. Heurística por CONTENIDO sobre las líneas AÑADIDAS del diff (las borradas no cuentan; los
     untracked cuentan enteros): ejecución dinámica de código (eval/exec), shell vía subprocess con
     shell activado, os.system/popen, inyección en el DOM (React incluido), deserialización
     insegura (pickle, yaml.load sin Loader), SQL concatenado o en f-string, secretos (API keys,
     claves privadas PEM), cabeceras de autorización y de cookies. La lista exacta es CONTENIDO
     (abajo). No se escanea el contenido de prosa (.md/.txt/.rst), de tests ni de fixtures
     (contienen payloads a propósito); la ruta sí se evalúa siempre. Binarios (NUL en la cabecera
     o «Binary files differ») se saltan.
  4. Config: `.claude/dev.json` → "revision": {"lenteSeguridad": "auto" | "siempre" | "nunca",
     "excluir": ["glob", …]} (default auto y sin exclusiones; fichero ausente/corrupto/valor
     desconocido → auto + aviso en stderr; `excluir` que no sea lista de cadenas → se ignora + aviso).

Uso:
  review-lens-select.py [--base <ref>] [--files f1 f2 …] [--json] [--root <dir>]
Salida: `lente_c: true|false` + motivos (tipo ruta|contenido|config, fichero, patrón, línea).
Exit: 0 SIEMPRE (nunca bloquea la revisión; ante error, aviso en stderr y lente_c: false).
"""
import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_BRANCHES = ("main", "master")
MODOS = ("auto", "siempre", "nunca")

# Stems anclados al inicio de token; los marcados con (?![a-z]) llevan además límite final porque son
# prefijo de palabras inocuas (tokenizer, helmet, aclimate…). Los demás siguen amplios a propósito
# (`sessions`, `oauth2`, `jwt_utils`, `passwd`, `secrets`, `cryptography`, `uploads`, `docker-compose`).
RUTA_RE = re.compile(
    r"(?<![a-z0-9])(auth(?!or)|login|sessions?|tokens?(?![a-z])|oauth|jwt|password|passwd|secrets?|crypt|"
    r"permissions?|acl(?![a-z])|rbac(?![a-z])|cors(?![a-z])|csrf|upload|payment|billing|docker|nginx|"
    r"k8s|helm(?![a-z]))"
    r"|(^|/)\.env(?=[^/]*$)|(^|/)Dockerfile(?=[^/]*$)|(^|/)\.github/workflows/",
    re.IGNORECASE)


def _load_glob_to_regex():
    """Reutiliza el traductor glob→regex de confluence-scope.py (`**/` = cero o más directorios, `*` =
    un nivel), fuente única de esa semántica en el repo (scope-check.py hace lo mismo); si la skill
    no está instalada, copia local equivalente."""
    cand = os.path.join(HERE, "..", "..", "confluence-publish", "scripts", "confluence-scope.py")
    if os.path.isfile(cand):
        try:
            spec = importlib.util.spec_from_file_location("confluence_scope", cand)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.glob_to_regex
        except Exception:  # noqa: BLE001 — degradación al traductor local
            pass

    def local(pattern):
        pattern = pattern.replace("\\", "/")
        out, i, n = [], 0, len(pattern)
        while i < n:
            if pattern[i:i + 3] == "**/":
                out.append("(?:.*/)?"); i += 3
            elif pattern[i:i + 2] == "**":
                out.append(".*"); i += 2
            elif pattern[i] == "*":
                out.append("[^/]*"); i += 1
            elif pattern[i] == "?":
                out.append("[^/]"); i += 1
            else:
                out.append(re.escape(pattern[i])); i += 1
        return re.compile("^" + "".join(out) + "$")
    return local


GLOB_TO_REGEX = _load_glob_to_regex()
DOCS_RE = re.compile(r"(^|/)docs/", re.IGNORECASE)

# (etiqueta, regex). Etiquetas y regex escritas para que ESTE fichero no se dispare a sí mismo
# (`[.]`, `[ ]`, etiquetas en kebab-case): un cambio en este script no debe forzar la Lente C.
CONTENIDO = [
    ("eval", re.compile(r"\beval\s*\(")),
    ("exec", re.compile(r"\bexec\s*\(")),
    ("subprocess-shell", re.compile(r"subprocess\b.*shell\s*=\s*True")),
    ("os-system", re.compile(r"\bos[.](system|popen)\s*\(")),
    ("inner-html", re.compile(r"\binner[H]TML\b")),
    ("dangerously-set-inner-html", re.compile(r"dangerouslySet[I]nnerHTML")),
    ("pickle-loads", re.compile(r"\bpickle[.]loads?\s*\(")),
    ("yaml-load", re.compile(r"\byaml[.]load\s*\(")),
    ("sql-concat", re.compile(r"SELECT\b.*\s[+]\s")),
    ("sql-fstring", re.compile(r"""f['"]\s*SELECT\b""")),
    ("api-key", re.compile(r"\bAPI[_]?KEY\b")),
    ("private-key", re.compile(r"PRIVATE[ ]KEY")),
    ("begin-rsa", re.compile(r"BEGIN[ ]RSA")),
    ("authorization-header", re.compile(r"Authorization[:]")),
    ("set-cookie", re.compile(r"Set[-]Cookie")),
]

PROSA_EXT = (".md", ".markdown", ".txt", ".rst")
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec|fixtures?)/|(^|/)test_[^/]*$|_test\.[^/]+$|\.(test|spec)\.[^/]+$",
                     re.IGNORECASE)


def avisar(msg):
    print(f"review-lens-select: {msg}", file=sys.stderr)


# ------------------------------------------------------------------ config ----

def leer_config(root):
    """Devuelve (modo, excluir[list[str]], avisos[list[str]]). Nunca lanza."""
    path = os.path.join(root, ".claude", "dev.json")
    if not os.path.isfile(path):
        return "auto", [], []
    try:
        with open(path, encoding="utf-8-sig") as f:
            cfg = json.load(f)
    except (OSError, ValueError) as e:
        return "auto", [], [f".claude/dev.json ilegible ({e.__class__.__name__}): lenteSeguridad = auto"]
    rev = cfg.get("revision") if isinstance(cfg, dict) else None
    if rev is None:
        return "auto", [], []
    if not isinstance(rev, dict):
        return "auto", [], [f".claude/dev.json revision = {rev!r} no es un objeto {{\"lenteSeguridad\": …}}: uso auto"]
    modo, avisos = "auto", []
    if "lenteSeguridad" in rev:
        val = rev.get("lenteSeguridad")
        if isinstance(val, str) and val.strip().lower() in MODOS:
            modo = val.strip().lower()
        else:
            avisos.append(f".claude/dev.json revision.lenteSeguridad = {val!r} desconocido (auto|siempre|nunca): uso auto")
    excluir = []
    if "excluir" in rev:
        ex = rev.get("excluir")
        if isinstance(ex, list) and all(isinstance(x, str) for x in ex):
            excluir = [re.sub(r"^(\./)+", "", x.replace("\\", "/").strip()) for x in ex if x.strip()]
        else:
            avisos.append(f".claude/dev.json revision.excluir = {ex!r} no es una lista de globs: se ignora")
    return modo, excluir, avisos


def leer_modo(root):
    """Compatibilidad: (modo, primer aviso|None)."""
    modo, _, avisos = leer_config(root)
    return modo, (avisos[0] if avisos else None)


def excluido_de_ruta(rel, excluir):
    """¿La ruta casa algún glob de `revision.excluir`? Solo afecta a la heurística de RUTA."""
    for g in excluir:
        try:
            if GLOB_TO_REGEX(g).match(rel):
                return True
        except re.error:
            continue
    return False


# --------------------------------------------------------------------- git ----

def git(root, *args):
    # core.quotepath=false: rutas no-ASCII tal cual (con el default git escribe "caf\303\251.py")
    r = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=root, capture_output=True,
                       text=True, errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def repo_root(path):
    try:
        return os.path.realpath(git(path, "rev-parse", "--show-toplevel").strip())
    except (RuntimeError, OSError):
        return None


def resolver_base(root, base):
    """(ref, descripción, aviso|None). Nunca lanza salvo --base inválido."""
    if base:
        git(root, "rev-parse", "--verify", "--quiet", base + "^{commit}")
        return base, f"--base {base}", None
    try:
        actual = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    except RuntimeError:
        return "HEAD", "HEAD (repo sin commits)", "repo sin commits: solo ficheros sin comitear"
    if actual in MAIN_BRANCHES:
        return "HEAD", f"HEAD (rama principal «{actual}»: solo cambios sin comitear)", None
    for b in MAIN_BRANCHES:
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", b], cwd=root,
                          capture_output=True).returncode == 0:
            mb = git(root, "merge-base", b, "HEAD").strip()
            return mb, f"merge-base {b}…HEAD ({mb[:8]})", None
    return "HEAD", "HEAD (sin main/master)", (f"no hay base clara (rama «{actual}», sin main/master): "
                                              f"solo cambios sin comitear — pasa `--base <ref>` para el rango completo")


def _sin_comillas(p):
    """Quita las comillas que git pone a rutas con espacios/caracteres especiales (`"a b.py"`)."""
    p = p.strip()
    if len(p) >= 2 and p[0] == '"' and p[-1] == '"':
        p = p[1:-1].replace('\\"', '"').replace("\\\\", "\\")
    return p


def tiene_commits(root):
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", "HEAD"], cwd=root,
                          capture_output=True).returncode == 0


def untracked(root):
    out = []
    for ln in git(root, "status", "--porcelain", "--untracked-files=all").splitlines():
        if ln.startswith("??"):
            p = _sin_comillas(ln[3:])
            if p:
                out.append(p)
    return out


def cambiados_git(root, base):
    """Ficheros cambiados (base…working tree) y untracked."""
    tracked = []
    if tiene_commits(root):
        tracked = [_sin_comillas(l) for l in git(root, "diff", "--name-only", base, "--").splitlines() if l.strip()]
    unt = untracked(root)
    return sorted(set(tracked) | set(unt)), set(unt)


def lineas_anadidas_git(root, base):
    """{fichero: [(nº línea nueva, texto)]} de las líneas '+' del diff base…working tree."""
    out, actual, nline, en_cabecera = {}, None, 0, False
    if not tiene_commits(root):
        return out
    for ln in git(root, "diff", "--no-color", "--unified=0", base, "--").splitlines():
        if ln.startswith("diff --git "):
            en_cabecera, actual = True, None
            continue
        # `+++` solo es cabecera dentro del preámbulo de `diff --git`; una línea añadida que empieza
        # por `++ x` aparece como `+++ x` en el cuerpo y NO debe tomarse por cabecera (gap M3)
        if en_cabecera and ln.startswith("+++ "):
            actual = _sin_comillas(ln[4:])
            actual = actual[2:] if actual.startswith("b/") else actual
            if actual == "/dev/null":
                actual = None
            en_cabecera = False
            continue
        if ln.startswith("@@"):
            en_cabecera = False
            m = re.search(r"\+(\d+)", ln)
            nline = int(m.group(1)) if m else 0
            continue
        if actual is None or ln.startswith(("---", "diff ", "index ", "Binary files", "old mode", "new mode",
                                            "similarity", "rename ", "new file", "deleted file")):
            continue
        if ln.startswith("+"):
            out.setdefault(actual, []).append((nline, ln[1:]))
            nline += 1
    return out


# ----------------------------------------------------------------- ficheros ----

def es_binario(path):
    try:
        with open(path, "rb") as f:
            return b"\x00" in f.read(8192)
    except OSError:
        return True


def lineas_fichero_entero(path):
    if not os.path.isfile(path) or es_binario(path):
        return []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return [(i, l.rstrip("\n")) for i, l in enumerate(f, 1)]
    except OSError:
        return []


def es_prosa(rel):
    return rel.lower().endswith(PROSA_EXT) or bool(DOCS_RE.search(rel))


def escanear_contenido(rel):
    """¿Se escanea el CONTENIDO de este fichero? Prosa/docs, tests y fixtures no."""
    return not es_prosa(rel) and not TEST_RE.search(rel)


def evaluar_ruta(rel):
    """¿Se evalúa la RUTA de este fichero? Prosa/docs no; tests sí (`tests/test_auth.py` cuenta)."""
    return not es_prosa(rel)


# ---------------------------------------------------------------- decisión ----

def motivos_de(ficheros, lineas_por_fichero, excluir=()):
    motivos = []
    for f in ficheros:
        m = RUTA_RE.search(f) if evaluar_ruta(f) and not excluido_de_ruta(f, excluir) else None
        if m:
            motivos.append({"tipo": "ruta", "fichero": f, "patron": m.group(0)})
        if not escanear_contenido(f):
            continue
        vistos = set()
        for nline, texto in lineas_por_fichero.get(f, []):
            for nombre, rx in CONTENIDO:
                if nombre in vistos:
                    continue
                if rx.search(texto):
                    vistos.add(nombre)
                    motivos.append({"tipo": "contenido", "fichero": f, "patron": nombre, "linea": nline})
    return motivos


def decidir(modo, motivos):
    if modo == "siempre":
        return True, [{"tipo": "config", "fichero": ".claude/dev.json", "patron": "lenteSeguridad: siempre"}] + motivos
    if modo == "nunca":
        return False, []
    return bool(motivos), motivos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None, help="ref base del diff (default: merge-base con main/master)")
    ap.add_argument("--files", nargs="*", default=None, help="ficheros a evaluar (sin git: se escanean enteros)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", default=".", help="raíz del proyecto (default: cwd)")
    args = ap.parse_args()

    avisos = []
    root = os.path.abspath(args.root)
    modo, excluir, avisos_cfg = leer_config(root)
    avisos.extend(avisos_cfg)

    base_desc, ficheros, lineas = "—", [], {}
    try:
        if args.files is not None:
            base_desc = "--files"
            ficheros = sorted({re.sub(r"^(\./)+", "", f.replace("\\", "/")) for f in args.files if f.strip()})
            lineas = {f: lineas_fichero_entero(os.path.join(root, f)) for f in ficheros}
        else:
            groot = repo_root(root)
            if not groot:
                avisos.append("fuera de un repositorio git y sin --files: no hay diff que evaluar (lente_c: false)")
            else:
                root_git = groot
                base, base_desc, av = resolver_base(root_git, args.base)
                if av:
                    avisos.append(av)
                ficheros, unt = cambiados_git(root_git, base)
                lineas = lineas_anadidas_git(root_git, base)
                for f in unt:
                    lineas[f] = lineas_fichero_entero(os.path.join(root_git, f))
    except Exception as e:  # noqa: BLE001 — nunca bloquea
        avisos.append(f"error evaluando el diff ({e.__class__.__name__}: {e}); lente_c: false")
        ficheros, lineas = [], {}

    motivos = motivos_de(ficheros, lineas, excluir) if ficheros else []
    lente_c, motivos = decidir(modo, motivos)

    for a in avisos:
        avisar(a)
    if args.json:
        print(json.dumps({"lente_c": lente_c, "modo": modo, "base": base_desc, "ficheros": len(ficheros),
                          "motivos": motivos, "avisos": avisos}, ensure_ascii=False, indent=2))
    else:
        print(f"review-lens-select: lente_c: {'true' if lente_c else 'false'} · modo {modo} · base {base_desc} · "
              f"{len(ficheros)} fichero(s) cambiado(s)")
        if motivos:
            print(f"motivos ({len(motivos)}):")
            for m in motivos:
                pos = f":{m['linea']}" if "linea" in m else ""
                print(f"   {m['tipo']:<9} {m['fichero']}{pos}  ~ {m['patron']}")
        else:
            print("motivos: —")
    return 0


if __name__ == "__main__":
    sys.exit(main())
