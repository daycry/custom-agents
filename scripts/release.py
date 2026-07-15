#!/usr/bin/env python3
"""release.py — sube la versión del plugin de forma COHERENTE en los tres sitios
donde vive (plugin.json y marketplace.json: metadata + entrada del plugin) y, de
forma opcional, hace commit + tag. Evita el fallo clásico de subir plugin.json y
olvidar marketplace.json, que deja a Claude sin ver la actualización.

Uso:
  python scripts/release.py 1.6.0            # bump en los 3 sitios + commit + tag v1.6.0
  python scripts/release.py 1.6.0 --no-git   # solo actualiza los ficheros
  python scripts/release.py --check          # verifica que las 3 versiones coinciden

Requiere Python 3 (stdlib). Pensado para ejecutarse en la máquina del autor, con
git configurado; el push se deja al usuario.
"""
import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, ".claude-plugin", "plugin.json")
MARKET = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
VERSION_RE = re.compile(r'("version"\s*:\s*")[^"]*(")')


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def current_versions():
    """Devuelve (plugin_version, marketplace_metadata_version, [plugin_entries])."""
    pv = json.loads(read(PLUGIN)).get("version")
    m = json.loads(read(MARKET))
    mv = m.get("metadata", {}).get("version")
    entries = [p.get("version") for p in m.get("plugins", [])]
    return pv, mv, entries


def all_versions():
    pv, mv, entries = current_versions()
    return [pv, mv, *entries]


def bump(new):
    for path in (PLUGIN, MARKET):
        text = read(path)
        new_text, n = VERSION_RE.subn(r"\g<1>" + new + r"\g<2>", text)
        if n == 0:
            sys.exit(f"ERROR: no encontré ningún campo \"version\" en {path}")
        json.loads(new_text)  # valida que sigue siendo JSON correcto
        write(path, new_text)
        print(f"  {os.path.relpath(path, ROOT)}: {n} campo(s) -> {new}")


def check():
    vs = all_versions()
    pv, mv, entries = current_versions()
    print(f"plugin.json           : {pv}")
    print(f"marketplace metadata  : {mv}")
    print(f"marketplace plugins   : {entries}")
    if len(set(v for v in vs if v is not None)) == 1 and None not in vs:
        print(f"OK: todas coinciden en {pv}")
        return 0
    print("ERROR: las versiones NO coinciden (o falta alguna)")
    return 1


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True)


def main():
    ap = argparse.ArgumentParser(description="Bump de versión coherente del plugin.")
    ap.add_argument("version", nargs="?", help="nueva versión, p. ej. 1.6.0")
    ap.add_argument("--no-git", action="store_true", help="no hacer commit ni tag")
    ap.add_argument("--check", action="store_true", help="solo verificar coherencia")
    args = ap.parse_args()

    if args.check or not args.version:
        sys.exit(check())

    new = args.version.lstrip("v")
    if not SEMVER.match(new):
        sys.exit(f"ERROR: '{new}' no es una versión semver X.Y.Z")

    cur = current_versions()[0]
    if new == cur:
        print(f"AVISO: la versión ya es {new}; no hay cambio.")
    print(f"Subiendo versión {cur} -> {new}:")
    bump(new)

    if check() != 0:
        sys.exit("ERROR: tras el bump las versiones no coinciden; revisa a mano.")

    if args.no_git:
        print("\nHecho (sin git). Recuerda commit + tag + push manuales.")
        return

    try:
        git("add", PLUGIN, MARKET)
        git("commit", "-m", f"chore: release v{new}")
        git("tag", f"v{new}")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        sys.exit(f"\nLos ficheros quedaron actualizados, pero git falló ({e}).\n"
                 f"Haz a mano: git add .claude-plugin/*.json && "
                 f"git commit -m 'chore: release v{new}' && git tag v{new}")
    print(f"\nHecho ✅ commit + tag v{new} creados. Ahora publica:")
    print(f"  git push origin HEAD && git push origin v{new}")


if __name__ == "__main__":
    main()
