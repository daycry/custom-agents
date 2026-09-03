#!/usr/bin/env python3
"""release.py — hace TODO el release mecánico del plugin de forma COHERENTE, para que no dependa
de la memoria de quien publica (las dos trampas del release v1.15.0 del 2026-09-02: `[Unreleased]`
sin mover en los dos CHANGELOG y `.sh` que llegaron desde Windows en modo 100644).

Qué hace `release.py X.Y.Z` (en este orden; si algo falla ANTES de escribir, no toca nada):
  0. Precondiciones: semver MAYOR que la actual (`--force-version` para saltarlo), repo git con el
     árbol LIMPIO (`git status --porcelain` vacío; `--allow-dirty` para saltarlo — si no, un
     CHANGELOG a medias se arrastraría al commit del release) y sin tag `vX.Y.Z` previo.
  1. Valida semver y calcula el movimiento del CHANGELOG bilingüe: el contenido de
     `## [Unreleased]` (EN) / `## [Sin publicar]` (ES) pasa a una sección nueva
     `## [X.Y.Z] - AAAA-MM-DD` justo debajo, la sección Unreleased queda vacía y se añade el enlace
     `[X.Y.Z]: …/releases/tag/vX.Y.Z` encima de los existentes. `[Unreleased]` VACÍO → aborta (un
     release sin notas es un error) salvo `--allow-empty-notes`. Si `## [X.Y.Z]` ya existe, no duplica.
  2. Checks previos (`--skip-checks` los salta): `scripts/lint_plugin.py` y `evals/check.py` deben
     pasar, las copias `*.MANUAL-COPY` coincidir, y `changelog-sync.py --check` se ejecuta como
     AVISO (iniciativas cerradas sin entrada en el CHANGELOG; nunca bloquea el release).
     salir 0; cada `*.MANUAL-COPY` (ficheros `<x>.yml.MANUAL-COPY` → `.github/workflows/<x>.yml`;
     carpeta `github-templates.MANUAL-COPY/` → `.github/`) coincide byte a byte con su copia; y se
     detectan los `.sh` versionados en modo 100644 (`git ls-files -s`).
  3. Bump de la versión en los TRES sitios (plugin.json; marketplace.json metadata + entrada).
  4. Escribe los dos CHANGELOG conservando su final de línea original (CRLF se mantiene CRLF).
  5. git: `update-index --chmod=+x` de los `.sh` en 100644 (avisando), `add` de manifiestos +
     CHANGELOG, `commit -m "chore: release vX.Y.Z"`, `tag vX.Y.Z`. El push se deja al usuario.
     (`--no-git` → solo ficheros, como siempre.)

  --dry-run   imprime el plan completo (secciones que movería, checks, chmod, commit, tag) sin tocar
              nada; un `[Unreleased]` vacío no lo corta: lo marca como «el release real ABORTARÍA aquí».
  --check     verifica coherencia: las 3 versiones coinciden Y la versión actual tiene su sección
              `## [X.Y.Z]` en AMBOS CHANGELOG.

Uso:
  python scripts/release.py 1.6.0                      # release completo + commit + tag v1.6.0
  python scripts/release.py 1.6.0 --dry-run            # muéstrame qué harías
  python scripts/release.py 1.6.0 --no-git             # solo ficheros
  python scripts/release.py 1.6.0 --skip-checks        # sin lint/evals/copias (no recomendado)
  python scripts/release.py 1.6.0 --allow-empty-notes  # aunque [Unreleased] esté vacío
  python scripts/release.py --check                    # coherencia versiones + CHANGELOG

Requiere Python 3 (stdlib). `--root DIR` permite ejecutarlo sobre otra copia (lo usan los tests).
"""
import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
VERSION_RE = re.compile(r'("version"\s*:\s*")[^"]*(")')
LINK_RE = re.compile(r"^\[(\d+\.\d+\.\d+)\]:\s+(\S+)\s*$", re.M)
LINK_BASE_DEFAULT = "https://github.com/daycry/custom-agents/releases/tag/v"
# (fichero, cabecera de la sección sin publicar, texto si se permite un release sin notas)
CHANGELOGS = (
    ("CHANGELOG.md", "## [Unreleased]", "_No notes._"),
    ("CHANGELOG.es.md", "## [Sin publicar]", "_Sin notas._"),
)
MANUAL_DIR = "github-templates.MANUAL-COPY"     # árbol → .github/ (distribution T-03)


class ReleaseError(Exception):
    pass


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def read_raw(p):
    """Texto con sus finales de línea ORIGINALES (sin traducción universal). Devuelve (texto_lf, crlf)."""
    with open(p, encoding="utf-8", newline="") as f:
        raw = f.read()
    crlf = "\r\n" in raw
    return raw.replace("\r\n", "\n"), crlf


def write_raw(p, s, crlf):
    """Escribe conservando el final de línea original del fichero (CRLF si lo tenía)."""
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s.replace("\n", "\r\n") if crlf else s)


# ------------------------------------------------------------------ versiones

def paths(root):
    return (os.path.join(root, ".claude-plugin", "plugin.json"),
            os.path.join(root, ".claude-plugin", "marketplace.json"))


def current_versions(root):
    """Devuelve (plugin_version, marketplace_metadata_version, [plugin_entries])."""
    plugin, market = paths(root)
    pv = json.loads(read(plugin)).get("version")
    m = json.loads(read(market))
    mv = m.get("metadata", {}).get("version")
    entries = [p.get("version") for p in m.get("plugins", [])]
    return pv, mv, entries


def bump(root, new, dry_run=False):
    for path in paths(root):
        text = read(path)
        new_text, n = VERSION_RE.subn(r"\g<1>" + new + r"\g<2>", text)
        if n == 0:
            raise ReleaseError(f"no encontré ningún campo \"version\" en {path}")
        json.loads(new_text)  # valida que sigue siendo JSON correcto
        if not dry_run:
            write(path, new_text)
        print(f"  {os.path.relpath(path, root)}: {n} campo(s) -> {new}")


def check_versions(root):
    pv, mv, entries = current_versions(root)
    vs = [pv, mv, *entries]
    print(f"plugin.json           : {pv}")
    print(f"marketplace metadata  : {mv}")
    print(f"marketplace plugins   : {entries}")
    if None not in vs and len(set(vs)) == 1:
        print(f"OK: todas coinciden en {pv}")
        return pv
    print("ERROR: las versiones NO coinciden (o falta alguna)")
    return None


# ------------------------------------------------------------------ changelog

def seccion_existe(text, version):
    return re.search(rf"^## \[{re.escape(version)}\]", text, re.M) is not None


def mover_unreleased(text, version, fecha, cabecera, placeholder, allow_empty=False, link_base=None):
    """Mueve el cuerpo de `cabecera` a `## [version] - fecha` y añade el enlace. Devuelve
    (texto_nuevo, resumen) con resumen = {ya_existia, movidas_lineas, enlace_añadido}."""
    if seccion_existe(text, version):
        return text, {"ya_existia": True, "movidas_lineas": 0, "enlace_añadido": False}
    lines = text.split("\n")
    try:
        i = next(k for k, ln in enumerate(lines) if ln.strip() == cabecera)
    except StopIteration:
        raise ReleaseError(f"no encuentro la sección `{cabecera}`")
    j = i + 1
    while j < len(lines) and not lines[j].startswith("## "):
        j += 1
    cuerpo = list(lines[i + 1:j])
    while cuerpo and not cuerpo[0].strip():
        cuerpo.pop(0)
    while cuerpo and not cuerpo[-1].strip():
        cuerpo.pop()
    if not cuerpo:
        if not allow_empty:
            raise ReleaseError(f"`{cabecera}` está VACÍO: un release sin notas es un error "
                               f"(escribe las notas o usa --allow-empty-notes)")
        cuerpo = [placeholder]
    nueva = [cabecera, "", f"## [{version}] - {fecha}", "", *cuerpo, ""]
    lines = lines[:i] + nueva + lines[j:]
    text = "\n".join(lines)
    # enlace: encima del primer `[X.Y.Z]: url` (misma base), o al final si no hay ninguno
    enlace_añadido = False
    if not re.search(rf"^\[{re.escape(version)}\]:", text, re.M):
        m = LINK_RE.search(text)
        if m:
            base = link_base or re.sub(r"\d+\.\d+\.\d+$", "", m.group(2))
            text = text[:m.start()] + f"[{version}]: {base}{version}\n" + text[m.start():]
        else:
            base = link_base or LINK_BASE_DEFAULT
            text = text.rstrip("\n") + f"\n\n[{version}]: {base}{version}\n"
        enlace_añadido = True
    return text, {"ya_existia": False, "movidas_lineas": len(cuerpo), "enlace_añadido": enlace_añadido}


def planificar_changelogs(root, version, fecha, allow_empty, dry_run=False):
    """[(ruta, texto_nuevo, resumen)] para los CHANGELOG que existen (resumen["crlf"] = final de línea original). Lanza ReleaseError si alguno
    tiene Unreleased vacío (y no allow_empty) — ANTES de escribir nada. En --dry-run el vacío no
    aborta: el plan lo marca como «el release real ABORTARÍA aquí» (resumen["abortaria"])."""
    out = []
    for nombre, cabecera, placeholder in CHANGELOGS:
        p = os.path.join(root, nombre)
        if not os.path.exists(p):
            print(f"⚠️  {nombre} no existe; se omite")
            continue
        texto, crlf = read_raw(p)
        try:
            nuevo, resumen = mover_unreleased(texto, version, fecha, cabecera, placeholder, allow_empty)
        except ReleaseError as e:
            if not dry_run:
                raise ReleaseError(f"{nombre}: {e}")
            nuevo, resumen = texto, {"ya_existia": False, "movidas_lineas": 0, "enlace_añadido": False,
                                     "abortaria": str(e)}
        resumen["crlf"] = crlf
        out.append((p, nuevo, resumen))
    return out


def check_changelogs(root, version):
    ok = True
    for nombre, _cab, _ph in CHANGELOGS:
        p = os.path.join(root, nombre)
        if not os.path.exists(p):
            continue
        if seccion_existe(read(p), version):
            print(f"{nombre:<16}: sección [{version}] presente")
        else:
            print(f"ERROR: {nombre} no tiene sección `## [{version}]`")
            ok = False
    return ok


# ------------------------------------------------------------------ checks previos

def _run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def run_checks(root):
    """lint_plugin.py + evals/check.py. Devuelve lista de fallos (vacía = ok); scripts ausentes → aviso."""
    fallos = []
    for rel in (os.path.join("scripts", "lint_plugin.py"), os.path.join("evals", "check.py")):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            print(f"⚠️  {rel} no existe; check omitido")
            continue
        r = _run([sys.executable, p], root)
        print(f"  {rel}: {'OK' if r.returncode == 0 else f'FALLA (exit {r.returncode})'}")
        if r.returncode != 0:
            fallos.append(f"{rel} salió con {r.returncode}:\n{(r.stdout + r.stderr).strip()[-2000:]}")
    return fallos


def aviso_changelog_sync(root):
    """`changelog-sync.py --check`: AVISO (no bloqueo) si hay ledgers cerrados sin entrada.

    Un release puede publicar deuda de notas a sabiendas; lo que no debe pasar es publicarla
    sin saberlo (superiority T-02).
    """
    cls = os.path.join(root, "skills", "changelog-sync", "scripts", "changelog-sync.py")
    if not os.path.exists(cls):
        return None
    r = _run([sys.executable, cls, "--check"], root)
    if r.returncode == 1:
        slugs = [ln.strip().lstrip("· ").split(" ")[0] for ln in r.stdout.splitlines()
                 if ln.strip().startswith("·")]
        return ("iniciativas cerradas sin entrada en el CHANGELOG: "
                + (", ".join(slugs) if slugs else "ver `changelog-sync.py --check`")
                + " — genera las notas con la skill `changelog-sync` (aviso, no bloquea)")
    return None


def _cmp(src, dst):
    if not os.path.isfile(dst):
        return "pendiente"
    with open(src, "rb") as a, open(dst, "rb") as b:
        return "ok" if a.read() == b.read() else "diff"


def manual_copies(root):
    """[(fuente_rel, destino_rel, estado)] con estado ∈ {'ok', 'diff', 'pendiente'}."""
    out = []
    for fn in sorted(os.listdir(root)):
        if fn.endswith(".yml.MANUAL-COPY") and os.path.isfile(os.path.join(root, fn)):
            dst = os.path.join(".github", "workflows", fn[:-len(".MANUAL-COPY")])
            out.append((fn, dst, _cmp(os.path.join(root, fn), os.path.join(root, dst))))
    d = os.path.join(root, MANUAL_DIR)
    if os.path.isdir(d):
        for dirpath, dirnames, filenames in os.walk(d):
            dirnames.sort()
            for f in sorted(filenames):
                src = os.path.join(dirpath, f)
                rel = os.path.relpath(src, d)
                dst = os.path.join(".github", rel)
                out.append((os.path.join(MANUAL_DIR, rel), dst, _cmp(src, os.path.join(root, dst))))
    return out


def en_git(root):
    r = _run(["git", "rev-parse", "--is-inside-work-tree"], root)
    return r.returncode == 0 and r.stdout.strip() == "true"


def arbol_sucio(root):
    """Líneas de `git status --porcelain` (vacío = árbol limpio)."""
    r = _run(["git", "status", "--porcelain"], root)
    return [ln for ln in r.stdout.splitlines() if ln.strip()] if r.returncode == 0 else []


def tag_existe(root, tag):
    return _run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], root).returncode == 0


def _tupla(v):
    return tuple(int(x) for x in v.split("."))


def sh_sin_ejecutable(root):
    """`.sh` versionados con modo 100644 (la trampa de Windows: core.fileMode=false)."""
    r = _run(["git", "ls-files", "-s"], root)
    if r.returncode != 0:
        return []
    out = []
    for ln in r.stdout.splitlines():
        partes = ln.split(None, 3)
        if len(partes) == 4 and partes[0] == "100644" and partes[3].endswith(".sh"):
            out.append(partes[3])
    return sorted(set(out))


# ------------------------------------------------------------------ main

def do_check(root):
    pv = check_versions(root)
    if not pv:
        return 1
    return 0 if check_changelogs(root, pv) else 1


def do_release(root, new, args):
    cur = current_versions(root)[0]
    if cur and SEMVER.match(cur) and _tupla(new) <= _tupla(cur):
        msg = f"la versión {new} no es mayor que la actual {cur}"
        if not args.force_version:
            raise ReleaseError(f"{msg} (un release va siempre hacia delante; --force-version para saltarlo)")
        print(f"⚠️  {msg} — continúo por --force-version")
    fecha = _dt.date.today().isoformat()
    git_ok = en_git(root)
    if not args.no_git and not git_ok:
        raise ReleaseError(f"{root} no es un repositorio git (usa --no-git para solo actualizar ficheros)")
    avisos_dry = []
    if git_ok and not args.no_git:
        sucio = arbol_sucio(root)
        if sucio and not args.allow_dirty:
            msg = ("el árbol de trabajo NO está limpio (se arrastraría al commit del release):\n    "
                   + "\n    ".join(sucio[:20]) + ("\n    …" if len(sucio) > 20 else "")
                   + "\n  comitea o guarda (git stash) esos cambios, o usa --allow-dirty")
            if not args.dry_run:
                raise ReleaseError(msg)
            avisos_dry.append(msg)
        if tag_existe(root, f"v{new}"):
            raise ReleaseError(f"el tag v{new} ya existe (git rev-parse --verify refs/tags/v{new}); "
                               f"bórralo (git tag -d v{new}) o elige otra versión")

    # 1. changelog (en memoria; aborta antes de escribir si Unreleased está vacío)
    planes = planificar_changelogs(root, new, fecha, args.allow_empty_notes, dry_run=args.dry_run)

    # 2. checks previos
    fallos = []
    if args.skip_checks:
        print("⚠️  --skip-checks: lint_plugin / evals/check / copias manuales NO se comprueban")
    else:
        print("Checks previos:")
        fallos.extend(run_checks(root))
        for src, dst, estado in manual_copies(root):
            if estado == "diff":
                fallos.append(f"copia manual atrasada: cp {src} {dst}")
            print(f"  {src} → {dst}: {estado}")
        av = aviso_changelog_sync(root)
        print(f"  changelog-sync --check: {'PENDIENTE' if av else 'OK'}")
        if av:
            print(f"  ⚠️  {av}")
    if fallos:
        raise ReleaseError("checks previos fallidos — nada se ha tocado:\n  - " + "\n  - ".join(fallos))
    sh_644 = sh_sin_ejecutable(root) if git_ok else []

    # 3. plan
    print(f"\nPlan release {cur} -> {new} ({fecha}):")
    for a in avisos_dry:
        print(f"  ⚠️  {a} → el release real ABORTARÍA aquí")
    for p, _nuevo, resumen in planes:
        nombre = os.path.relpath(p, root)
        if resumen.get("abortaria"):
            print(f"  ⚠️  {nombre}: {resumen['abortaria']} → el release real ABORTARÍA aquí")
        elif resumen["ya_existia"]:
            print(f"  {nombre}: la sección [{new}] ya existe; no se toca")
        else:
            print(f"  {nombre}: mover {resumen['movidas_lineas']} línea(s) de Unreleased a `## [{new}] - {fecha}`"
                  + (" + enlace" if resumen["enlace_añadido"] else ""))
    for sh in sh_644:
        print(f"  ⚠️  {sh} está en modo 100644 → git update-index --chmod=+x")
    if not args.no_git:
        print(f"  git add manifiestos + CHANGELOG · commit 'chore: release v{new}' · tag v{new}")
    if args.dry_run:
        bump(root, new, dry_run=True)
        print("\n--dry-run: no se ha tocado nada.")
        return 0

    # 4. escribir
    print("\nAplicando:")
    bump(root, new)
    for p, nuevo, resumen in planes:
        if not resumen["ya_existia"]:
            write_raw(p, nuevo, resumen["crlf"])
            print(f"  {os.path.relpath(p, root)}: sección [{new}] creada" + (" (CRLF conservado)" if resumen["crlf"] else ""))
    if not check_versions(root):
        raise ReleaseError("tras el bump las versiones no coinciden; revisa a mano.")
    if args.no_git:
        if sh_644:
            print("⚠️  .sh en modo 100644 (corrígelos con git update-index --chmod=+x): " + ", ".join(sh_644))
        print("\nHecho (sin git). Recuerda commit + tag + push manuales.")
        return 0

    # 5. git
    plugin, market = paths(root)
    a_añadir = [plugin, market] + [p for p, _n, _r in planes]
    try:
        for sh in sh_644:
            subprocess.run(["git", "update-index", "--chmod=+x", sh], cwd=root, check=True)
            try:                                   # y el fichero en disco (en Linux/macOS, si no, status lo marcaría)
                fp = os.path.join(root, sh)
                os.chmod(fp, os.stat(fp).st_mode | 0o111)
            except OSError:
                pass
            print(f"  ⚠️  {sh}: modo 100644 → 100755 (git update-index --chmod=+x)")
        subprocess.run(["git", "add", *a_añadir], cwd=root, check=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root).returncode == 0:
            print("  (nada que comitear: los ficheros ya estaban así; solo se crea el tag)")
        else:
            subprocess.run(["git", "commit", "-q", "-m", f"chore: release v{new}"], cwd=root, check=True)
        subprocess.run(["git", "tag", f"v{new}"], cwd=root, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise ReleaseError(f"los ficheros quedaron actualizados, pero git falló ({e}).\n"
                           f"Haz a mano: git add .claude-plugin/*.json CHANGELOG*.md && "
                           f"git commit -m 'chore: release v{new}' && git tag v{new}")
    print(f"\nHecho ✅ commit + tag v{new} creados. Ahora publica:")
    print(f"  git push origin HEAD && git push origin v{new}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Release mecánico y coherente del plugin.")
    ap.add_argument("version", nargs="?", help="nueva versión, p. ej. 1.6.0")
    ap.add_argument("--no-git", action="store_true", help="no hacer commit ni tag")
    ap.add_argument("--check", action="store_true", help="verificar coherencia (versiones + CHANGELOG)")
    ap.add_argument("--dry-run", action="store_true", help="mostrar el plan sin tocar nada")
    ap.add_argument("--skip-checks", action="store_true", help="saltar lint_plugin / evals/check / copias manuales")
    ap.add_argument("--allow-empty-notes", action="store_true", help="permitir [Unreleased] vacío")
    ap.add_argument("--allow-dirty", action="store_true", help="permitir árbol de trabajo con cambios sin comitear")
    ap.add_argument("--force-version", action="store_true", help="permitir una versión menor o igual que la actual")
    ap.add_argument("--root", default=ROOT, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    root = os.path.abspath(args.root)

    try:
        if args.check or not args.version:
            return do_check(root)
        new = args.version.lstrip("v")
        if not SEMVER.match(new):
            raise ReleaseError(f"'{new}' no es una versión semver X.Y.Z")
        return do_release(root, new, args)
    except ReleaseError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
