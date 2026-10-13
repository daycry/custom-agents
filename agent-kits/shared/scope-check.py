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
  4-bis. Criterios aprobados: compara las líneas `- [ ]`/`- [x]` de cada tarea con las del `tasks.md`
     de la LÍNEA BASE (el de la base del diff; si ahí no existe, el del primer commit de la rama que
     lo contiene). Un criterio reescrito o borrado —o su tarea desaparecida— es `criterios_alterados`
     y cuenta para el exit code: quien implementa no edita el criterio que debe cumplir. Marcar la
     casilla, AMPLIAR el texto detrás (`(fix1: …)`, una nota) o añadir criterios nuevos no cuenta.
     Solo mira la primera línea de cada criterio. Sin línea base (ledger nunca comiteado) → línea ℹ️,
     sin fallo.
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
Exit: 0 nada fuera de alcance · 1 hay ficheros fuera o criterios aprobados alterados (con --warn-only siempre 0) ·
      2 error de uso (carpeta/ledger inválidos, sin git en el PATH, fuera de un repo, un `.git`
      presente con `git rev-parse` fallando —config rota, `safe.directory`, repo corrupto: se cita
      el stderr de git—, sin base determinable: el mensaje distingue los cinco, porque el remedio
      no es el mismo).
"""
import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

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


# ------------------------------------------- criterios de aceptación aprobados ----
def _norm_criterio(texto):
    return re.sub(r"\s+", " ", texto).strip().rstrip(" .;:")


def _conserva(criterio, actuales):
    """El criterio sigue si alguna línea actual ES su texto o lo AMPLÍA detrás en frontera de
    palabra (`(fix1: …)`, una nota): ampliar no debilita; reescribir o borrar, sí puede."""
    n = len(criterio)
    return any(a == criterio or (a.startswith(criterio) and not (a[n].isalnum() or a[n] == "_"))
               for a in actuales)


def criterios_alterados(base_text, cur_text, parse_ledger):
    """[{tarea, criterio}] de la línea base que ya no siguen en SU tarea (reescritos, borrados o la
    tarea desaparecida). Marcar la casilla, ampliar el texto o añadir criterios nuevos no cuenta."""
    actuales = {t["id"]: [_norm_criterio(c) for c in t.get("criterios", [])]
                for t in parse_ledger(cur_text)["tareas"]}
    out = []
    for t in parse_ledger(base_text)["tareas"]:
        for c in t.get("criterios", []):
            n = _norm_criterio(c)
            if n and not _conserva(n, actuales.get(t["id"], [])):
                out.append({"tarea": t["id"], "criterio": n})
    return out


def _git_show(root, ref, rel):
    r = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=root, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return r.stdout if r.returncode == 0 else None


def linea_base_ledger(root, base, tasks_rel):
    """(texto, descripción) del `tasks.md` aprobado o (None, None): el de la base del diff y, si ahí
    no existe, el del PRIMER commit de la rama que lo contiene (el plan suele entrar con la rama)."""
    texto = _git_show(root, base, tasks_rel)
    if texto is not None:
        return texto, f"base del diff ({base[:12]})"
    for c in git(root, "log", "--reverse", "--format=%H", f"{base}..HEAD", "--", tasks_rel,
                 check=False).split():
        texto = _git_show(root, c, tasks_rel)
        if texto is not None:
            return texto, f"primer commit de la rama con el ledger ({c[:12]})"
    return None, None


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


# --------------------------------------------------- commit projection ----
def _commit_git(root, *args, data=None, filters=(), check=True):
    """Byte reads only; never refresh the index or invoke configured transformers."""
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
    overrides = ["-c", "core.fsmonitor=false"]
    for name in filters:
        for option, value in (("clean", ""), ("process", ""), ("smudge", ""), ("required", "false")):
            overrides.extend(["-c", f"filter.{name}.{option}={value}"])
    result = subprocess.run(["git", *overrides, "--literal-pathspecs", *args],
                            cwd=root, env=env, input=data, capture_output=True, timeout=20)
    if check and result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout


COMMIT_FILE_BYTES = 8 * 1024 * 1024
COMMIT_TOTAL_BYTES = 32 * 1024 * 1024
_COMMIT_READER = None


def _commit_reader():
    global _COMMIT_READER
    if _COMMIT_READER is None:
        spec = importlib.util.spec_from_file_location("commit_local_read", os.path.join(HERE, "local-read.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _COMMIT_READER = module
    return _COMMIT_READER


def _commit_paths(root, seleccion, check_files=True):
    if not isinstance(seleccion, list) or not seleccion:
        raise ValueError("selección vacía o inválida")
    base = Path(os.path.abspath(root))
    seen = set()
    for path in seleccion:
        if (not isinstance(path, str) or not path or "\0" in path or "\\" in path or ":" in path
                or path.startswith(("/", ":")) or re.match(r"^[A-Za-z]:", path)
                or any(part in ("", ".", "..") for part in path.split("/"))
                or path.split("/")[0].lower() == ".git"):
            raise ValueError("ruta relativa literal inválida")
        key = os.path.normcase(path)
        target = base / path
        if key in seen:
            raise ValueError("ruta duplicada")
        if check_files:
            try:
                info, _ = _commit_reader()._checked(base, target)
                if stat.S_ISDIR(info.st_mode):
                    raise ValueError("directorio seleccionado")
            except FileNotFoundError:
                pass  # A tracked deletion is a legitimate literal selection.
        seen.add(key)
    return base


def _commit_records(raw, tree=False):
    records = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        info, path = record.split(b"\t", 1)
        fields = info.decode("ascii").split()
        name = path.decode("utf-8", errors="surrogateescape")
        mode, oid, stage = (fields[0], fields[2], "0") if tree else fields
        records.setdefault(name, []).append({"mode": mode, "blob": oid, "stage": stage})
    return records


def _commit_digest(snapshot):
    body = {k: v for k, v in snapshot.items() if k != "snapshot_id"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def proyectar_commit(root, seleccion):
    """Project an exact literal selection, without staging or writing objects.

    Custom filters are deliberately unsupported; their commands are disabled for
    every child read, including paths outside the selection. Snapshot integrity
    does not authenticate an actor or lock out concurrent editors.
    """
    base = _commit_paths(root, seleccion)
    configured = _commit_git(base, "config", "--null", "--get-regexp", r"^filter\.", check=False)
    filters = sorted({r.split(b"\n", 1)[0].decode("utf-8").rsplit(".", 1)[0][7:]
                      for r in configured.split(b"\0") if r})
    def read(*args, data=None, check=True):
        return _commit_git(base, *args, data=data, filters=filters, check=check)
    head = read("rev-parse", "HEAD").strip().decode("ascii")
    index_path = Path(os.fsdecode(read("rev-parse", "--git-path", "index").strip()))
    if not index_path.is_absolute():
        index_path = base / index_path
    index_sha = hashlib.sha256(index_path.read_bytes()).hexdigest()
    index = _commit_records(read("ls-files", "--stage", "-z"))
    tree = _commit_records(read("ls-tree", "-r", "-z", "HEAD"), tree=True)
    others = [os.fsdecode(p) for p in read("ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p]
    paths = sorted(set(index) | set(tree) | set(others) | set(seleccion))
    attrs = read("check-attr", "-z", "--stdin", "filter", "working-tree-encoding",
                 data=b"".join(os.fsencode(p) + b"\0" for p in paths)).split(b"\0")
    unsupported = {}
    for i in range(0, len(attrs) - 1, 3):
        path, attr, value = attrs[i:i+3]
        if value not in (b"unspecified", b"unset"):
            unsupported[os.fsdecode(path)] = "custom_filter_unsupported" if attr == b"filter" else "encoding_unsupported"
    selected, conflicts, limits, staged, changed = [], [], [], [], set(others)
    safe_patch, native_names, consumed = [], [], 0
    local = _commit_reader()
    core_filemode = read("config", "--bool", "--get", "core.filemode", check=False).strip() == b"true"
    for path in paths:
        h = (tree.get(path) or [None])[0]
        entries = index.get(path, [])
        entry = entries[0] if len(entries) == 1 and entries[0]["stage"] == "0" else None
        intent = False
        if entry and h is None:
            debug = read("ls-files", "--debug", "-z", "--", path)
            flags = re.search(rb"flags: ([0-9a-fA-F]+)", debug)
            intent = bool(flags and int(flags[1], 16) & 0x20000000)
        target = base / path
        staged_difference = not intent and (entry != h or bool(entries) and entry is None)
        if staged_difference and entries:
            staged.extend({"path": path, **e} for e in entries)
        elif h and not entries:
            staged.append({"path": path, "blob": None, "mode": None, "stage": "0"})
        if staged_difference or h is None:
            changed.add(path)
        if path in unsupported:
            (conflicts if path in seleccion else limits).append({"path": path, "code": unsupported[path]})
        if path not in seleccion:
            # Metadata only. Git supplies changed names; Python never opens an
            # unselected body, nor hashes it to infer ownership/content.
            if path in index and path not in unsupported:
                try:
                    info, _ = local._checked(base, target)
                    if stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                        native_names.append(path)
                    else:
                        limits.append({"path": path, "code": "unselected_unavailable"})
                        changed.add(path)
                except FileNotFoundError:
                    changed.add(path)
                except (OSError, ValueError):
                    limits.append({"path": path, "code": "unselected_unavailable"})
                    changed.add(path)
            continue
        if staged_difference:
            conflicts.append({"path": path, "code": "staged_conflict"})
        if h is None and entry is None:
            conflicts.append({"path": path, "code": "new_unregistered"})
        raw, sha, blob, mode, info, blocked = None, None, None, None, None, False
        try:
            info, _ = local._checked(base, target)
            if not stat.S_ISREG(info.st_mode):
                conflicts.append({"path": path, "code": "selected_unavailable"}); blocked = True
            elif info.st_nlink != 1:
                conflicts.append({"path": path, "code": "selected_hardlink"}); blocked = True
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            conflicts.append({"path": path, "code": "selected_unavailable"}); blocked = True
        if entry and entry["mode"] not in ("100644", "100755"):
            conflicts.append({"path": path, "code": "file_type_unsupported"}); blocked = True
        # Budget both observed worktree bytes and the HEAD side of its patch.
        head_size = int(read("cat-file", "-s", h["blob"]).strip()) if h else 0
        size = info.st_size if info else 0
        if max(size, head_size) > COMMIT_FILE_BYTES or consumed + size + head_size > COMMIT_TOTAL_BYTES:
            conflicts.append({"path": path, "code": "selected_too_large"}); blocked = True
        if info and not blocked:
            observed = local.read_bytes(base, path, max_bytes=min(COMMIT_FILE_BYTES, COMMIT_TOTAL_BYTES-consumed-head_size),
                                        include_digest=True, include_identity=True)
            consumed += observed['bytes'] + head_size
            if observed['status'] != 'ok':
                code = "selected_too_large" if observed['status'] == 'too_large' else "selected_unavailable"
                conflicts.append({"path": path, "code": code}); blocked = True
            else:
                after, _ = local._checked(base, target)
                # Compare generations within the same stat API. On Windows,
                # descriptor and path ctime need not represent the same clock.
                if (after.st_nlink != 1 or local._identity(after) != observed['identity']
                        or local._generation(after) != local._generation(info)
                        or local._generation(after)[:2] != observed['generation'][:2]):
                    conflicts.append({"path": path, "code": "selected_unavailable"}); blocked = True
                else:
                    raw, sha = observed['data'], observed['sha256']
                    mode = ("100755" if core_filemode and after.st_mode & 0o100 else "100644")
                    if not core_filemode and entry:
                        mode = entry['mode']
                    if path not in unsupported:
                        blob = read("hash-object", "--path=" + path, "--stdin", data=raw).strip().decode("ascii")
        elif not info and not blocked:
            consumed += head_size
        if not blocked and path not in unsupported:
            safe_patch.append(path)
        selected.append({"path": path, "estado": "eliminado" if info is None else "nuevo" if h is None else "modificado",
                         "head_blob": h["blob"] if h else None, "index_blob": entry["blob"] if entry else None,
                         "head_mode": h["mode"] if h else None, "index_mode": entry["mode"] if entry else None,
                         "worktree_mode": mode, "worktree_sha256": sha, "blob_commit": blob})
    selected.sort(key=lambda row: seleccion.index(row["path"]))
    # Keep argv bounded on Windows; each batch is literal names only. Filters
    # are disabled, unsafe filesystem entries excluded before native diff.
    batch, batch_bytes = [], 0
    for path in native_names + [None]:
        size = len(os.fsencode(path)) + 3 if path is not None else 0
        if batch and (path is None or batch_bytes + size > 6000):
            changed.update(os.fsdecode(p) for p in read("diff", "--no-ext-diff", "--no-textconv", "--name-only", "-z", "HEAD", "--", *batch).split(b"\0") if p)
            batch, batch_bytes = [], 0
        if path is not None:
            batch.append(path); batch_bytes += size
    patch = read("diff", "--no-ext-diff", "--no-textconv", "--binary", "HEAD", "--", *safe_patch) if safe_patch else b""
    try:
        display, lossless = patch.decode("utf-8"), True
    except UnicodeDecodeError:
        display, lossless = patch.decode("utf-8", errors="backslashreplace"), False
    snapshot = {"schema_version": 1, "head": head, "index_sha256": index_sha,
                "seleccionados": selected, "no_seleccionados": sorted(changed - set(seleccion)),
                "staged_ajenos": [row for row in staged if row["path"] not in seleccion],
                "conflictos": conflicts, "limites": limits, "patch": display,
                "patch_base64": base64.b64encode(patch).decode("ascii"),
                "patch_sha256": hashlib.sha256(patch).hexdigest(), "patch_display_lossless": lossless}
    snapshot["snapshot_id"] = _commit_digest(snapshot)
    return snapshot


def validar_seleccion_commit(root, snapshot):
    """Re-read the boundary; malformed/tampered snapshots never become a new choice."""
    invalid = {"valido": False, "motivos": [{"code": "invalid_snapshot"}]}
    try:
        required = {"schema_version", "head", "index_sha256", "seleccionados", "no_seleccionados",
                    "staged_ajenos", "conflictos", "limites", "patch", "patch_base64",
                    "patch_sha256", "patch_display_lossless", "snapshot_id"}
        if not isinstance(snapshot, dict) or set(snapshot) != required or type(snapshot["schema_version"]) is not int or snapshot["schema_version"] != 1:
            return invalid
        def digest_value(value, lengths=(64,)):
            return isinstance(value, str) and len(value) in lengths and re.fullmatch(r"[0-9a-f]+", value) is not None
        if not digest_value(snapshot["head"], (40, 64)) or not all(digest_value(snapshot[field]) for field in ("index_sha256", "patch_sha256", "snapshot_id")):
            return invalid
        if not isinstance(snapshot["seleccionados"], list) or not snapshot["seleccionados"]:
            return invalid
        row_keys = {"path", "estado", "head_blob", "index_blob", "head_mode", "index_mode",
                    "worktree_mode", "worktree_sha256", "blob_commit"}
        for row in snapshot["seleccionados"]:
            if not isinstance(row, dict) or set(row) != row_keys or row["estado"] not in ("nuevo", "modificado", "eliminado"):
                return invalid
            if any(row[field] is not None and not digest_value(row[field], (40, 64)) for field in ("head_blob", "index_blob", "blob_commit")):
                return invalid
            if row["worktree_sha256"] is not None and not digest_value(row["worktree_sha256"]):
                return invalid
            if any(row[field] is not None and not re.fullmatch(r"[0-7]{6}", row[field]) for field in ("head_mode", "index_mode", "worktree_mode")):
                return invalid
        if _commit_digest(snapshot) != snapshot["snapshot_id"]:
            return invalid
        patch = base64.b64decode(snapshot["patch_base64"], validate=True)
        try:
            display, lossless = patch.decode("utf-8"), True
        except UnicodeDecodeError:
            display, lossless = patch.decode("utf-8", errors="backslashreplace"), False
        if hashlib.sha256(patch).hexdigest() != snapshot["patch_sha256"] or display != snapshot["patch"] or type(snapshot["patch_display_lossless"]) is not bool or lossless != snapshot["patch_display_lossless"]:
            return invalid
        paths = [row["path"] for row in snapshot["seleccionados"]]
        _commit_paths(root, paths, check_files=False)
        if not all(isinstance(snapshot[field], list) for field in ("no_seleccionados", "staged_ajenos", "conflictos", "limites")):
            return invalid
        if not all(isinstance(path, str) for path in snapshot["no_seleccionados"]):
            return invalid
        if not all(isinstance(row, dict) and isinstance(row.get("code"), str) and isinstance(row.get("path"), str) for row in snapshot["conflictos"] + snapshot["limites"]):
            return invalid
        if not all(isinstance(row, dict) and set(row) == {"path", "mode", "blob", "stage"}
                   and isinstance(row["path"], str) and row["stage"] in ("0", "1", "2", "3")
                   and (row["blob"] is None or digest_value(row["blob"], (40, 64)))
                   and (row["mode"] is None or re.fullmatch(r"[0-7]{6}", row["mode"]))
                   for row in snapshot["staged_ajenos"]):
            return invalid
    except (ValueError, TypeError, KeyError, AttributeError, RecursionError):
        return invalid
    try:
        current = proyectar_commit(root, paths)
    except ValueError:
        return {"valido": False, "motivos": [{"code": "selected_unavailable"}]}
    except (OSError, RuntimeError, subprocess.SubprocessError):
        return {"valido": False, "motivos": [{"code": "projection_unavailable"}]}
    reasons = list(current["conflictos"])
    for field, code in (("head", "head_changed"), ("index_sha256", "index_changed")):
        if current[field] != snapshot[field]:
            reasons.append({"code": code})
    for old, now in zip(snapshot["seleccionados"], current["seleccionados"]):
        if old != now:
            reasons.append({"code": "selected_changed", "path": old["path"]})
    if current["patch_sha256"] != snapshot["patch_sha256"] and not any(r["code"] == "selected_changed" for r in reasons):
        reasons.append({"code": "selected_changed"})
    if any(current[field] != snapshot[field] for field in ("staged_ajenos", "no_seleccionados", "limites", "conflictos")):
        reasons.append({"code": "view_changed"})
    return {"valido": not reasons, "motivos": reasons}


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
    base_text, criterios_base = linea_base_ledger(root, base, tasks_rel)
    alterados = criterios_alterados(base_text, text, parse_ledger) if base_text is not None else []
    if base_text is None:
        info.append("criterios: sin línea base (tasks.md no está en la base del diff ni en ningún commit "
                    "de la rama) — comitea el plan aprobado para que la puerta vigile sus criterios")
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
                          "criterios_base": criterios_base, "criterios_alterados": alterados,
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
        if alterados:
            print(f"❌ criterios aprobados alterados ({len(alterados)}, línea base: {criterios_base}):" +
                  "".join(f"\n   {a['tarea']}: «{a['criterio']}»" for a in alterados))
            print("→ el criterio que se cumple no lo reescribe quien lo cumple: restaura el texto (puedes "
                  "marcarlo o ampliarlo detrás) o, si lo cambió planner/el usuario, rebátelo con esa evidencia.")
    if (fuera or alterados) and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
