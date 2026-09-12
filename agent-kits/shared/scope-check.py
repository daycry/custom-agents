#!/usr/bin/env python3
"""
scope-check.py — comprobación DETERMINISTA de alcance del diff de una iniciativa.

(Iniciativa deterministic-guardrails: sustituye el check manual «git status / git diff --stat
solo dentro del alcance» del DoD del implementer y se ejecuta en /dev-cycle Fase 3 ANTES de
lanzar las dos lentes de revisión — un fichero fuera de alcance vuelve al implementer como gap
Important sin gastar revisores.)

Qué hace:
  1. Ficheros cambiados = `git diff --name-only <base> HEAD` ∪ `git status --porcelain`
     (comiteado + staged + sin comitear + sin seguimiento).
     base: `--base <ref>`; si no, merge-base con `main`/`master` (el que exista); si la rama
     actual ES la principal, base = HEAD (solo cambios sin comitear); si nada de eso → exit 2
     con mensaje (hay que pasar `--base`).
  2. Alcance declarado = campos `- **Archivos**:` de TODAS las tareas del ledger `tasks.md`
     (tokens entre acentos graves; globs `*` (un nivel) y `**/` (cero o más directorios),
     llaves `{a,b}`, carpetas con `/` final o existentes, «(nuevo)» y otros apuntes entre
     paréntesis se ignoran, listas por coma).
     Siempre en alcance: el propio `tasks.md` de la iniciativa y `docs/knowledge/**` —CON UNA
     EXCEPCIÓN: `docs/knowledge/journal/**`, que no lo escribe nadie de la cadena sino el hook de
     sesión, va en las exclusiones por defecto del punto 3 y sale como «excluido», no como «en
     alcance». Lo que «siempre en alcance» garantiza es que un glob de USUARIO (`dev.json`) no
     puede sacar la memoria del proyecto del alcance; la exclusión por defecto del journal sí.
  3. Excluidos: lo que no es de ninguna tarea porque lo escribe el orquestador o una herramienta
     (`EXCLUIR_DEFAULT`: `CONTINUE-HERE*.md`, `.claude/**`, `docs/knowledge/journal/**`), ampliable
     de forma ADITIVA con `.claude/dev.json` → "alcance": {"excluir": ["glob", …]} (misma
     semántica de glob que `revision.excluir`). Un fichero DECLARADO en un campo `Archivos` gana
     a la exclusión, e igual `SIEMPRE_EN_ALCANCE` (`docs/knowledge/**`): NO se pueden excluir desde
     `dev.json`. Los excluidos no son «fuera de alcance» (no cambian el exit code) pero se listan,
     con el glob que los excluyó, para que la revisión los vea.
  4. Clasifica: en alcance · fuera de alcance · excluidos · declarados sin tocar.
  5. Publica SIEMPRE (stderr + clave `info` del `--json`) la línea ℹ️ con lo que esconden los
     globs de USUARIO —fichero y glob, sin umbral y sin los del default—, para que el implementer y
     la revisión comprueben que lo excluido es lo que se quería excluir. No es un gap: es
     visibilidad. En el `--json`, `excluidos_usuario` da la misma lista ya separada de
     `excluidos_patron`, donde los dos tipos de glob van mezclados.
  6. Avisa (stderr + clave `avisos` del `--json`) cuando la exclusión DE USUARIO está apagando la
     puerta: si deja la lista «fuera de alcance» vacía ESCONDIENDO el grueso del trabajo, o si un
     glob de usuario se come una fracción desproporcionada del diff (≥ UMBRAL_FRACCION, con al menos
     UMBRAL_MINIMO ficheros). Los dos umbrales se miden sobre los ficheros cambiados que NO excluye
     el default del plugin. El aviso no cambia el exit code —la exclusión puede ser legítima— pero
     deja de ser silenciosa. Una exclusión legítima que se limita a quitar ruido no avisa nunca: si
     avisara en cada pasada verde sería un gap Important perpetuo e imposible de cerrar (R4a-29).

Uso:
  scope-check.py <docs/roadmap/<fecha>-<slug>> [--base <ref>] [--warn-only] [--json]
Exit: 0 nada fuera de alcance · 1 hay ficheros fuera (con --warn-only siempre 0) ·
      2 error de uso (carpeta/ledger inválidos, sin git en el PATH, fuera de un repo, un `.git`
      presente con `git rev-parse` fallando —config rota, `safe.directory`, repo corrupto: se cita
      el stderr de git—, sin base determinable: el mensaje distingue los cinco, porque el remedio
      no es el mismo).
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
MAIN_BRANCHES = ("main", "master")
SIEMPRE_EN_ALCANCE = ("docs/knowledge/",)

# Lo que NO es de ninguna tarea: lo escribe el orquestador (bitácora de sesión), la instalación
# (`.claude/` del consumidor: config, estado del meter, cachés) o un hook (journal). Deliberadamente
# MÍNIMA: excluir de más convierte la puerta en decorativa, así que aquí no entra `docs/**` ni nada
# del código. Se amplía por proyecto con `dev.json` `alcance.excluir` (aditivo, nunca sustituye).
EXCLUIR_DEFAULT = ("CONTINUE-HERE*.md", ".claude/**", "docs/knowledge/journal/**")

# Cuándo la exclusión de usuario deja de ser un ajuste y empieza a ser un apagado de la puerta.
UMBRAL_FRACCION = 0.5     # fracción del diff que un solo glob de usuario puede comerse sin aviso
UMBRAL_MINIMO = 3         # …a partir de este nº de ficheros (por debajo, un diff pequeño no dice nada)


def _load_glob_to_regex():
    """Reutiliza el traductor glob→regex de confluence-scope.py (`**/` = cero o más directorios,
    `*` = un nivel), la fuente única de esa semántica en el repo; si la skill no está instalada,
    copia local equivalente (fnmatch trata `**` como `*` y exigía un nivel — gap de la revisión)."""
    cand = os.path.join(HERE, "..", "..", "skills", "confluence-publish", "scripts", "confluence-scope.py")
    if os.path.isfile(cand):
        try:
            spec = importlib.util.spec_from_file_location("confluence_scope", cand)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.glob_to_regex
        except Exception:  # noqa: BLE001 — degradación al traductor local
            pass

    # --8<-- glob_to_regex (respaldo local) — REPLICADO LITERAL en agent-kits/shared/scope-check.py y
    # skills/adversarial-review/scripts/review-lens-select.py; el canónico de la semántica es
    # skills/confluence-publish/scripts/confluence-scope.py (otra forma: no comparable byte a byte).
    # DECLARADO en agent-kits/shared/copias.json (ADR-016); tests/test_copias_declaradas.py compara
    # estas dos copias byte a byte: no lo edites en una sola.
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
    # --8<-- fin glob_to_regex (respaldo local)
    return local


GLOB_TO_REGEX = _load_glob_to_regex()


def leer_excluir(root):
    """Devuelve (patrones, avisos, de_usuario) = `EXCLUIR_DEFAULT` + `.claude/dev.json`
    `alcance.excluir`; `de_usuario` son solo los que vienen de `dev.json` (los que pueden apagar
    la puerta, y los únicos sobre los que se avisa).

    Carga TOLERANTE (misma forma que `review-lens-select.py:leer_config`): nunca lanza; fichero
    ausente, ilegible o clave mal formada → default + aviso. La ampliación es ADITIVA: el default
    no se puede vaciar desde `dev.json`."""
    patrones = list(EXCLUIR_DEFAULT)
    path = os.path.join(root, ".claude", "dev.json")
    if not os.path.isfile(path):
        return patrones, [], []
    try:
        with open(path, encoding="utf-8-sig") as f:
            cfg = json.load(f)
    except (OSError, ValueError) as e:
        return patrones, [f".claude/dev.json ilegible ({e.__class__.__name__}): uso las exclusiones por defecto"], []
    alc = cfg.get("alcance") if isinstance(cfg, dict) else None
    if alc is None:
        return patrones, [], []
    if not isinstance(alc, dict):
        return patrones, [f".claude/dev.json alcance = {alc!r} no es un objeto {{\"excluir\": [\"glob\", …]}}: "
                          f"uso las exclusiones por defecto"], []
    if "excluir" not in alc:
        return patrones, [], []
    ex = alc.get("excluir")
    if not (isinstance(ex, list) and all(isinstance(x, str) for x in ex)):
        return patrones, [f".claude/dev.json alcance.excluir = {ex!r} no es una lista de globs: se ignora "
                          f"(siguen las exclusiones por defecto)"], []
    de_usuario = []
    for x in ex:
        g = re.sub(r"^(\./)+", "", x.replace("\\", "/").strip())
        if g and g not in patrones:
            patrones.append(g)
            de_usuario.append(g)
    return patrones, [], de_usuario


def patron_excluyente(path, excluir):
    """El PRIMER glob de exclusión que casa la ruta, o None (`**` = cero o más directorios,
    `*` = un nivel). Devolver el patrón —y no un booleano— es lo que permite publicarlo en el
    `--json` y distinguir una exclusión legítima del default de una puerta apagada a mano."""
    for g in excluir:
        try:
            if GLOB_TO_REGEX(g).match(path) or (g.endswith("/") and path.startswith(g)):
                return g
        except re.error:          # glob que no traduce: se ignora, nunca rompe la puerta
            continue
    return None


def excluido(path, excluir):
    """¿La ruta casa algún glob de exclusión? (envoltorio booleano de `patron_excluyente`)."""
    return patron_excluyente(path, excluir) is not None


def _load_parse_ledger():
    spec = importlib.util.spec_from_file_location("ledger_lint", os.path.join(HERE, "ledger-lint.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.parse_ledger


# ------------------------------------------------------------------- git ----
def git(root, *args, check=True):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def git_disponible():
    """¿Hay un ejecutable `git` en el PATH?

    `repo_root` devuelve None en los dos casos —sin git y fuera de un repo— y quien llama atribuía
    la causa al segundo, con lo que el remedio que sugería («esto no es un repositorio git»: haz
    `git init`) no arreglaba el primero (gap R4a-34). Con esta función, el mensaje puede decir cuál
    de los dos es."""
    return shutil.which("git") is not None


def hay_git_dir(path):
    """¿Hay un `.git` (carpeta o fichero de worktree) en `path` o en alguno de sus padres?

    Lo pregunta al SISTEMA DE FICHEROS, no a git: es la única forma de saber que la carpeta SÍ es
    un repositorio cuando `git rev-parse` falla por una razón que no es «no es un repositorio»
    (gap B4-2)."""
    p = os.path.abspath(path)
    while True:
        if os.path.exists(os.path.join(p, ".git")):
            return True
        padre = os.path.dirname(p)
        if padre == p:
            return False
        p = padre


def repo_root_detalle(path):
    """(raíz del repo o None, stderr de git o None).

    `repo_root` se queda con la raíz y TIRA el stderr; quien tiene que explicar el fallo lo
    necesita (gap B4-2): `git rev-parse` también falla con un repo perfectamente presente cuando
    la configuración está rota, cuando falta un `safe.directory` («detected dubious ownership»)
    o cuando el repo está corrupto, y en esos tres casos el mensaje de git ES el diagnóstico."""
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=path, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
    except OSError as e:
        return None, str(e)
    if r.returncode != 0:
        return None, (r.stderr or "").strip() or None
    return r.stdout.strip() or None, None


def repo_root(path):
    return repo_root_detalle(path)[0]


def motivo_sin_repo(path):
    """Por qué `repo_root(path)` ha dado None, en una frase con el remedio que toca.

    TRES causas, no dos (gap B4-2): sin `git` en el PATH no hay nada que inicializar; con git y sin
    `.git` por ningún lado, la carpeta de verdad no es un repositorio; y con git y CON `.git`, el
    fallo es de git —config rota, `safe.directory`, repo corrupto— y el remedio está en su stderr,
    que hasta ahora se tragaba y mandaba al usuario a hacer un `git init` sobre un repo que ya
    existe. La usan `scope-check` y —vía `getattr`, arista E12— `agent-kits/qa/coverage-check.py`."""
    if not git_disponible():
        return ("no hay `git` en el PATH: la puerta no puede leer el diff — instala git (o añádelo "
                "al PATH) y repite")
    _, err = repo_root_detalle(path)
    if hay_git_dir(path):
        detalle = f": «{err}»" if err else " sin mensaje"
        return (f"hay un `.git` en esta carpeta o en alguna de sus padres, pero `git rev-parse` "
                f"falla{detalle} — NO es que falte el repositorio: arregla lo que dice git (config "
                f"rota, `safe.directory` de una carpeta de otro usuario, repo corrupto) y repite")
    return "esto no es un repositorio git"


def resolver_base(root, base):
    """Devuelve (ref, descripción) o lanza RuntimeError con mensaje claro."""
    if base:
        git(root, "rev-parse", "--verify", "--quiet", base + "^{commit}")
        return base, f"--base {base}"
    actual = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if actual in MAIN_BRANCHES:
        return "HEAD", f"HEAD (rama principal «{actual}»: solo cambios sin comitear)"
    for b in MAIN_BRANCHES:
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", b], cwd=root,
                          capture_output=True).returncode == 0:
            mb = git(root, "merge-base", b, "HEAD").strip()
            return mb, f"merge-base {b}…HEAD ({mb[:8]})"
    raise RuntimeError(
        f"no hay base clara: la rama «{actual}» no es main/master y no existe ninguna de las dos "
        f"en el repo — pasa `--base <ref>` (p. ej. el commit desde el que partió la rama).")


def ficheros_cambiados(root, base):
    out = set()
    if base != "HEAD":
        out.update(l.strip() for l in git(root, "diff", "--name-only", base, "HEAD").splitlines() if l.strip())
    for ln in git(root, "status", "--porcelain", "--untracked-files=all").splitlines():
        if len(ln) < 4:
            continue
        p = ln[3:]
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        p = p.strip().strip('"')
        if p:
            out.add(p.rstrip("/"))
    return sorted(out)


# --------------------------------------------------------------- ledger ----
_TOKEN_RE = re.compile(r"`([^`\n]+)`")
_PATH_OK = re.compile(r"^[\w./*?\[\]{},~@+\-]+$")


def _expandir_llaves(tok):
    m = re.search(r"\{([^{}]*)\}", tok)
    if not m:
        return [tok]
    out = []
    for alt in m.group(1).split(","):
        out.extend(_expandir_llaves(tok[:m.start()] + alt.strip() + tok[m.end():]))
    return out


def patrones_del_ledger(text, parse_ledger):
    """[(patrón, T-XX)] a partir de los campos Archivos de cada tarea (tokens en acentos graves)."""
    parsed = parse_ledger(text)
    ids = [t["id"] for t in parsed["tareas"]]
    patrones = []
    # trocear por cabeceras de tarea para atribuir cada campo a su T-XX
    chunks = re.split(r"^(?=###\s+T-\d+\b)", text, flags=re.M)
    for ch in chunks:
        m = re.match(r"###\s+(T-\d+)\b", ch)
        tid = m.group(1) if m and m.group(1) in ids else None
        if not tid:
            continue
        for ln in ch.splitlines():
            if not re.match(r"^\s*-\s*\*\*Archivos\*\*\s*:", ln):
                continue
            campo = ln.split(":", 1)[1]
            for tok in _TOKEN_RE.findall(campo):
                tok = tok.strip().replace("\\", "/")
                tok = re.sub(r"^\./", "", tok)
                if not tok or " " in tok or not _PATH_OK.match(tok):
                    continue          # «sus tests», «CI», frases… no son rutas
                if tok.startswith("/"):
                    continue          # rutas absolutas fuera del repo (/tmp/…) no cuentan
                for p in _expandir_llaves(tok):
                    patrones.append((p, tid))
    return patrones


def casa(path, patron, root):
    pat = patron.rstrip("/")
    if patron.endswith("/") or os.path.isdir(os.path.join(root, pat)):
        return path == pat or path.startswith(pat + "/")
    if any(c in pat for c in "*?"):
        return GLOB_TO_REGEX(pat).match(path) is not None   # `*` un nivel · `**/` cero o más directorios
    return path == pat


def clasificar(cambiados, patrones, tasks_rel, root, excluir=(), excluir_usuario=()):
    """(en alcance, fuera, excluidos, declarados sin tocar, {excluido: glob que lo excluyó}).

    Orden de precedencia, de más fuerte a más débil: declarado en `Archivos` (o el propio ledger)
    → exclusión POR DEFECTO (la curada por el plugin: el journal que escribe el hook sigue fuera)
    → `SIEMPRE_EN_ALCANCE` → exclusión DE USUARIO → fuera de alcance. `SIEMPRE_EN_ALCANCE` va antes
    que la exclusión de usuario a propósito: `docs/knowledge/**` es memoria del proyecto y no se
    puede sacar del alcance con un glob de `dev.json` (antes, un `docs/**` en `alcance.excluir`
    mandaba un ADR nuevo de `en_alcance` a `excluidos`)."""
    en, fuera, excl, usados, quien = [], [], [], set(), {}
    for f in cambiados:
        hit = [i for i, (p, _) in enumerate(patrones) if casa(f, p, root)]
        usados.update(hit)          # también si el fichero ya está en alcance «de oficio»
        g = patron_excluyente(f, excluir)
        if hit or f == tasks_rel:
            en.append(f)            # declarado explícitamente (o el ledger): gana a la exclusión
        elif g is not None and g not in excluir_usuario:
            excl.append(f)          # exclusión por defecto: ni en alcance ni fuera
            quien[f] = g
        elif any(f.startswith(p) for p in SIEMPRE_EN_ALCANCE):
            en.append(f)            # memoria del proyecto: no la excluye un glob de `dev.json`
        elif g is not None:
            excl.append(f)
            quien[f] = g
        else:
            fuera.append(f)
    sin_tocar = sorted({f"{p} ({t})" for i, (p, t) in enumerate(patrones) if i not in usados})
    return en, fuera, excl, sin_tocar, quien


def avisos_de_exclusion(cambiados, fuera, quien, excluir_usuario):
    """Avisos cuando la exclusión DE USUARIO (la de `dev.json`, no el default) está apagando la
    puerta en vez de quitarle ruido. Nunca cambia el exit code: informa.

    **Denominador** (gap R4a-39): la fracción se mide sobre los ficheros cambiados que NO excluye el
    default del plugin. Contarlos diluía la señal y APAGABA el aviso escondiendo exactamente lo
    mismo: tocar `CONTINUE-HERE.md` y tres ficheros de `.claude/` bajaba un 3 de 6 (50 %) a un 3 de
    10 (30 %) sin cambiar una coma del glob sospechoso.

    **Umbral del primer aviso** (gap R4a-29): que la lista «fuera de alcance» quede vacía NO basta.
    Un proyecto con un `alcance.excluir` legítimo que toca uno o dos ficheros de su propio ruido en
    una pasada por lo demás verde disparaba el ⚠️ en CADA pasada; como el DoD del `implementer` y la
    §0 de `adversarial-review` mandan tratar todo ⚠️ como gap Important, era un Important PERPETUO
    que solo se podía cerrar borrando la configuración. El aviso exige ahora que la exclusión de
    usuario esté haciendo el trabajo pesado —los mismos dos umbrales que el aviso de anchura—: por
    debajo, el glob se limita a quitar ruido ya previsto y la puerta calla. Los dos avisos siguen
    mirando SOLO ficheros no declarados en ningún campo `Archivos`: lo declarado gana a la exclusión
    en `clasificar`, así que nunca llega hasta aquí."""
    avisos = []
    if not excluir_usuario or not cambiados:
        return avisos
    por_defecto = {f for f, g in quien.items() if g not in excluir_usuario}
    relevantes = [f for f in cambiados if f not in por_defecto]
    por_usuario = sorted(f for f, g in quien.items() if g in excluir_usuario)
    if not por_usuario or not relevantes:
        return avisos
    n_rel = len(relevantes)

    def desproporcionado(n):
        return n >= UMBRAL_MINIMO and n >= UMBRAL_FRACCION * n_rel

    if not fuera and desproporcionado(len(por_usuario)):
        avisos.append(
            f"`alcance.excluir` de .claude/dev.json deja la lista «fuera de alcance» VACÍA: "
            f"{len(por_usuario)} de los {n_rel} fichero(s) cambiados relevantes (sin contar los que "
            f"excluye el default) saldrían fuera y los esconde un glob de usuario "
            f"({', '.join(por_usuario[:5])}{'…' if len(por_usuario) > 5 else ''}). "
            f"La puerta pasa, pero pasa porque la has apagado: revisa que la exclusión sea "
            f"deliberada y no un `**` de más.")
    for g in excluir_usuario:
        n = sum(1 for f, gg in quien.items() if gg == g)
        if desproporcionado(n):
            avisos.append(
                f"el glob de usuario «{g}» excluye {n} de los {n_rel} ficheros cambiados relevantes "
                f"({n * 100 // n_rel} %): una exclusión de esa anchura convierte la puerta "
                f"en decorativa — acótala o declara esos ficheros en el campo `Archivos` de su tarea.")
    return avisos


def excluidos_por_usuario(quien, excluir_usuario):
    """{fichero: glob de USUARIO que lo excluyó}, sin los que excluye el default del plugin.

    El `--json` publicaba `excluidos_patron` con los dos tipos de glob mezclados y la distinción
    —cuál viene de `.claude/dev.json` y cuál del default curado— había que rehacerla en cada
    consumidor cruzando con `excluir_usuario`. Aquí se hace UNA vez (gap B4-1)."""
    return {f: g for f, g in sorted(quien.items()) if g in excluir_usuario}


def info_de_exclusion(quien, excluir_usuario):
    """Línea ℹ️ con lo que esconden los globs de USUARIO. SIEMPRE que escondan algo, sin umbral.

    Es la otra mitad del gap B4-1, y a propósito NO es un aviso ⚠️: el ⚠️ desproporcionado pide un
    umbral porque el DoD lo trata como gap Important, y bajar ese umbral a «uno o dos ficheros»
    devolvía el Important perpetuo de R4a-29. Pero callar del todo por debajo del umbral dejaba un
    glob que esconde dos ficheros de producción SIN rastro. La salida es **visibilidad en vez de
    veredicto**: el exit code y el ⚠️ no se tocan, y la lista se publica siempre para que el
    implementer y la revisión COMPRUEBEN que lo excluido es lo que se quería excluir. Discriminar
    por «no declarado en `Archivos`» no servía: lo declarado gana a la exclusión en `clasificar`,
    así que nunca llega hasta aquí."""
    de_usuario = excluidos_por_usuario(quien, excluir_usuario)
    if not de_usuario:
        return []
    detalle = ", ".join(f"{f} ({g})" for f, g in de_usuario.items())
    return [f"`alcance.excluir` de .claude/dev.json esconde {len(de_usuario)} fichero(s) del "
            f"recuento (no cuentan para el exit code; entre paréntesis, el glob de usuario que los "
            f"excluyó): {detalle}. No es un gap: comprueba que es EXACTAMENTE lo que querías "
            f"excluir."]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("iniciativa", help="carpeta docs/roadmap/<fecha>-<slug>")
    ap.add_argument("--base", default=None, help="ref base del diff (default: merge-base con main/master)")
    ap.add_argument("--warn-only", action="store_true", help="siempre exit 0 (solo informa)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    carpeta = os.path.abspath(args.iniciativa)
    tasks = os.path.join(carpeta, "tasks.md")
    if not os.path.isfile(tasks):
        print(f"scope-check: no existe {tasks}", file=sys.stderr)
        return 2
    root = repo_root(carpeta)
    if not root:
        # TRES causas, tres remedios distintos (gaps R4a-34 y B4-2): sin `git` en el PATH no hay
        # nada que inicializar; sin `.git` por ningún lado no hay repositorio; y con `.git` presente
        # el que falla es git, y su stderr es el diagnóstico. Decir «no es un repositorio» en los
        # tres casos mandaba al usuario a hacer un `git init` inútil
        print(f"scope-check: {motivo_sin_repo(carpeta)}", file=sys.stderr)
        return 2
    root = os.path.realpath(root)
    tasks_rel = os.path.relpath(os.path.realpath(tasks), root).replace("\\", "/")
    slug = os.path.basename(carpeta)
    try:
        base, base_desc = resolver_base(root, args.base)
        cambiados = ficheros_cambiados(root, base)
    except RuntimeError as e:
        print(f"scope-check: {e}", file=sys.stderr)
        return 2

    parse_ledger = _load_parse_ledger()
    text = open(tasks, encoding="utf-8", errors="replace").read()
    patrones = patrones_del_ledger(text, parse_ledger)
    excluir, avisos, excluir_usuario = leer_excluir(root)
    en, fuera, excl, sin_tocar, quien = clasificar(cambiados, patrones, tasks_rel, root,
                                                   excluir, excluir_usuario)
    avisos += avisos_de_exclusion(cambiados, fuera, quien, excluir_usuario)
    info = info_de_exclusion(quien, excluir_usuario)
    for a in avisos:
        print(f"scope-check: ⚠️  {a}", file=sys.stderr)
    for i in info:      # por stderr, para que salga también con --json (gap B4-1)
        print(f"scope-check: ℹ️  {i}", file=sys.stderr)

    if args.json:
        print(json.dumps({"slug": slug, "base": base, "base_desc": base_desc, "cambiados": len(cambiados),
                          "en_alcance": en, "fuera_de_alcance": fuera, "declarados_sin_tocar": sin_tocar,
                          "patrones": [p for p, _ in patrones], "excluidos": excl,
                          "excluir_vigente": excluir, "excluir_usuario": excluir_usuario,
                          "excluidos_patron": quien,
                          "excluidos_usuario": excluidos_por_usuario(quien, excluir_usuario),
                          "avisos": avisos, "info": info},
                         ensure_ascii=False, indent=2))
    else:
        print(f"scope-check: {slug} · base {base_desc} · {len(cambiados)} fichero(s) cambiado(s) · "
              f"{len(patrones)} patrón(es) declarados en Archivos")
        print(f"✅ en alcance ({len(en)}):" + ("".join(f"\n   {f}" for f in en) or " —"))
        print(f"❌ fuera de alcance ({len(fuera)}):" + ("".join(f"\n   {f}" for f in fuera) or " —"))
        if excl:
            print(f"ℹ️  excluidos ({len(excl)}, no cuentan para el exit code; entre paréntesis, el "
                  f"glob que los excluyó):" +
                  "".join(f"\n   {f}  ({quien.get(f, '?')})" for f in excl))
        if sin_tocar:
            print(f"ℹ️  declarados sin tocar ({len(sin_tocar)}):" + "".join(f"\n   {f}" for f in sin_tocar))
        if fuera:
            print("→ o el fichero es necesario (añádelo al campo Archivos de su tarea y anótalo) "
                  "o revierte el cambio; hasta entonces la revisión no arranca.")
    if fuera and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
