#!/usr/bin/env python3
"""
deps-inventory.py — inventario DETERMINISTA de dependencias de un proyecto (skill
`dependency-upgrade`, iniciativa memory-health). Nunca actualiza nada ni inventa versiones.

  1. Detecta manifiestos y sus lockfiles (recorrido del árbol, fuera `vendor/`, `node_modules/`…):
       npm      package.json            ↔ package-lock.json · yarn.lock · pnpm-lock.yaml
       composer composer.json           ↔ composer.lock
       pip      requirements*.txt       ↔ (sin lock propio; Pipfile.lock si existe)
       python   pyproject.toml          ↔ poetry.lock · uv.lock · pdm.lock
       go       go.mod                  ↔ go.sum
       bundler  Gemfile                 ↔ Gemfile.lock
       nuget    *.csproj                ↔ packages.lock.json
  2. Lista cada dependencia con la versión DECLARADA (tal cual: `^1.2.0`, `>=2,<3`, `~> 5.1`) y, si el
     lockfile es parseable (`package-lock.json`, `composer.lock`, `Gemfile.lock`, `go.sum`), la BLOQUEADA.
     En `requirements*.txt` el marcador de entorno (`; python_version > "3.8"`) va en su campo `marcador`,
     los comentarios `#` se descartan, y `-e .` / `git+https://…` / `nombre @ url` aparecen como
     dependencias `tipo: local|vcs|url` sin versión ni `latest` (no desaparecen); las opciones de pip
     (`-r`, `-c`, `--index-url`…) no son dependencias.
  3. Si la herramienta del ecosistema está en PATH (y no se pasa `--no-outdated`), ejecuta su
     «outdated» oficial con timeout y lo parsea: `npm outdated --json`, `composer outdated --format=json`,
     `pip list --outdated --format=json`, `go list -u -m -json all`. Sin herramienta o sin red →
     `latest = —` y AVISO explícito. **Jamás se rellena `latest` a mano.**
  4. Clasifica el salto declarada→latest por semver: `patch` · `minor` · `major` (→ «breaking probable:
     leer changelog/UPGRADING upstream») · `igual` · `desconocido` (no comparable).

Uso:  deps-inventory.py <ruta> [--json] [--no-outdated] [--timeout 60]
Exit: 0 siempre (inventario emitido, aunque no haya manifiestos) · 2 error de uso (ruta inexistente).
"""
import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

EXCLUDE_DIRS = {"vendor", "node_modules", "dist", "build", ".git", "__pycache__", ".venv", "venv",
                "target", ".next", "coverage", "bin", "obj"}
LOCKS = {
    "npm": ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "npm-shrinkwrap.json"],
    "composer": ["composer.lock"],
    "pip": ["Pipfile.lock"],
    "python": ["poetry.lock", "uv.lock", "pdm.lock"],
    "go": ["go.sum"],
    "bundler": ["Gemfile.lock"],
    "nuget": ["packages.lock.json"],
}
TOOLS = {   # ecosistema → (binario, argumentos de outdated)
    "npm": ("npm", ["outdated", "--json"]),
    "composer": ("composer", ["outdated", "--format=json"]),
    "pip": ("pip", ["list", "--outdated", "--format=json"]),
    "python": ("pip", ["list", "--outdated", "--format=json"]),
    "go": ("go", ["list", "-u", "-m", "-json", "all"]),
}
_VER = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?")


# ------------------------------------------------------------------ detección

def manifiestos(root):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = sorted(d for d in dns if d not in EXCLUDE_DIRS and not d.startswith("."))
        for fn in sorted(fns):
            eco = None
            if fn == "package.json":
                eco = "npm"
            elif fn == "composer.json":
                eco = "composer"
            elif re.match(r"^requirements[\w.-]*\.txt$", fn):
                eco = "pip"
            elif fn == "pyproject.toml":
                eco = "python"
            elif fn == "go.mod":
                eco = "go"
            elif fn == "Gemfile":
                eco = "bundler"
            elif fn.endswith(".csproj"):
                eco = "nuget"
            if eco:
                p = os.path.join(dp, fn)
                locks = [l for l in LOCKS.get(eco, []) if os.path.isfile(os.path.join(dp, l))]
                out.append({"ecosistema": eco, "manifiesto": os.path.relpath(p, root).replace(os.sep, "/"),
                            "dir": dp, "lockfiles": locks})
    return out


def _leer(path):
    try:
        return open(path, encoding="utf-8-sig", errors="replace").read()
    except OSError:
        return None


def _json(path):
    t = _leer(path)
    if t is None:
        return None
    try:
        return json.loads(t)
    except ValueError:
        return None


# ------------------------------------------------------------------ declaradas

def declaradas(m, avisos):
    """[(nombre, versión declarada, grupo)] del manifiesto; avisa si es ilegible."""
    p = os.path.join(m["dir"], os.path.basename(m["manifiesto"]))
    eco = m["ecosistema"]
    out = []
    if eco == "npm":
        d = _json(p)
        if not isinstance(d, dict):
            avisos.append(f"{m['manifiesto']}: JSON ilegible")
            return out
        for grupo in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
            for k, v in sorted((d.get(grupo) or {}).items()):
                out.append((k, str(v), grupo))
    elif eco == "composer":
        d = _json(p)
        if not isinstance(d, dict):
            avisos.append(f"{m['manifiesto']}: JSON ilegible")
            return out
        for grupo in ("require", "require-dev"):
            for k, v in sorted((d.get(grupo) or {}).items()):
                if k == "php" or k.startswith("ext-"):
                    continue
                out.append((k, str(v), grupo))
    elif eco == "pip":
        t = _leer(p) or ""
        for line in t.splitlines():
            s = line.split(" #", 1)[0].split("\t#", 1)[0].strip()      # comentario de fin de línea fuera
            if s.startswith("#"):
                s = ""
            if not s or s.startswith(("-r", "--requirement", "-c", "--constraint", "-i", "--index-url",
                                      "--extra-index-url", "-f", "--find-links", "--")):
                continue                                              # opciones de pip: no son dependencias
            # T-fix1 (M3): `-e .` / `-e ./pkg` → tipo local; `git+…`/`hg+…`/`svn+…`/`bzr+…` o `nombre @ url` → vcs/url
            if s.startswith(("-e ", "--editable ")):
                ref = s.split(None, 1)[1].strip()
                if re.match(r"^(git|hg|svn|bzr)\+", ref):
                    nombre = re.search(r"#egg=([A-Za-z0-9_.\-]+)", ref)
                    out.append((nombre.group(1) if nombre else ref, "*", "requirements", {"tipo": "vcs", "origen": ref}))
                else:
                    out.append((ref, "*", "requirements", {"tipo": "local", "origen": ref}))
                continue
            if re.match(r"^(git|hg|svn|bzr)\+", s) or re.match(r"^https?://", s):
                nombre = re.search(r"#egg=([A-Za-z0-9_.\-]+)", s)
                out.append((nombre.group(1) if nombre else s, "*", "requirements", {"tipo": "vcs" if "+" in s.split(":", 1)[0] else "url", "origen": s}))
                continue
            marcador = ""
            if ";" in s:
                s, marcador = (x.strip() for x in s.split(";", 1))
            if " @ " in s:
                nombre, origen = (x.strip() for x in s.split(" @ ", 1))
                out.append((re.sub(r"\[.*\]", "", nombre), "*", "requirements",
                            {"tipo": "vcs" if re.match(r"^(git|hg|svn|bzr)\+", origen) else "url", "origen": origen, "marcador": marcador}))
                continue
            mm = re.match(r"^([A-Za-z0-9_.\-]+)(\[[^\]]*\])?\s*(.*)$", s)
            if mm:
                extra = {"marcador": marcador} if marcador else {}
                out.append((mm.group(1), mm.group(3).strip() or "*", "requirements", extra))
    elif eco == "python":
        try:
            import tomllib
            d = tomllib.loads(_leer(p) or "")
        except Exception:  # noqa: BLE001 — sin tomllib (<3.11) o TOML roto
            avisos.append(f"{m['manifiesto']}: TOML ilegible (¿python < 3.11?)")
            return out
        for dep in (d.get("project") or {}).get("dependencies") or []:
            mm = re.match(r"^([A-Za-z0-9_.\-]+)(\[.*?\])?\s*(.*)$", str(dep))
            if mm:
                out.append((mm.group(1), mm.group(3).strip() or "*", "project.dependencies"))
        for grupo, deps in ((d.get("project") or {}).get("optional-dependencies") or {}).items():
            for dep in deps:
                mm = re.match(r"^([A-Za-z0-9_.\-]+)(\[.*?\])?\s*(.*)$", str(dep))
                if mm:
                    out.append((mm.group(1), mm.group(3).strip() or "*", f"optional.{grupo}"))
        poetry = ((d.get("tool") or {}).get("poetry") or {})
        for grupo, deps in (("dependencies", poetry.get("dependencies") or {}),
                            ("dev-dependencies", poetry.get("dev-dependencies") or {})):
            for k, v in sorted(deps.items()):
                if k.lower() == "python":
                    continue
                ver = v.get("version", "*") if isinstance(v, dict) else str(v)
                out.append((k, str(ver), f"poetry.{grupo}"))
    elif eco == "go":
        t = _leer(p) or ""
        bloque = False
        for line in t.splitlines():
            s = line.split("//", 1)[0].strip()
            if s.startswith("require ("):
                bloque = True
                continue
            if bloque and s == ")":
                bloque = False
                continue
            mm = re.match(r"^(?:require\s+)?(\S+)\s+(v\S+)(\s+// indirect)?$", s) if (bloque or s.startswith("require ")) else None
            if mm:
                out.append((mm.group(1), mm.group(2), "indirect" if "indirect" in line else "require"))
    elif eco == "bundler":
        t = _leer(p) or ""
        for line in t.splitlines():
            mm = re.match(r"""^\s*gem\s+['"]([^'"]+)['"](?:\s*,\s*['"]([^'"]+)['"])*""", line)
            if mm:
                vers = re.findall(r"""['"]([~><=!]*\s*\d[^'"]*)['"]""", line)
                out.append((mm.group(1), ", ".join(vers) if vers else "*", "gem"))
    elif eco == "nuget":
        t = _leer(p) or ""
        for tag in re.finditer(r"<PackageReference\b[^>]*>", t):
            inc = re.search(r'Include="([^"]+)"', tag.group(0))
            ver = re.search(r'Version="([^"]+)"', tag.group(0))
            if inc:
                out.append((inc.group(1), ver.group(1) if ver else "*", "PackageReference"))
    return out


# ------------------------------------------------------------------ bloqueadas (lockfiles parseables)

def bloqueadas(m):
    d, out = m["dir"], {}
    if "package-lock.json" in m["lockfiles"]:
        lock = _json(os.path.join(d, "package-lock.json")) or {}
        for k, v in (lock.get("packages") or {}).items():
            if k.startswith("node_modules/") and k.count("node_modules/") == 1 and isinstance(v, dict) and v.get("version"):
                out[k[len("node_modules/"):]] = v["version"]
        for k, v in (lock.get("dependencies") or {}).items():          # lockfileVersion 1
            if isinstance(v, dict) and v.get("version"):
                out.setdefault(k, v["version"])
    if "composer.lock" in m["lockfiles"]:
        lock = _json(os.path.join(d, "composer.lock")) or {}
        for grupo in ("packages", "packages-dev"):
            for pkg in lock.get(grupo) or []:
                if isinstance(pkg, dict) and pkg.get("name"):
                    out[pkg["name"]] = str(pkg.get("version", "")).lstrip("v")
    if "Gemfile.lock" in m["lockfiles"]:
        for mm in re.finditer(r"^\s{4}([A-Za-z0-9_\-.]+) \(([^)]+)\)$", _leer(os.path.join(d, "Gemfile.lock")) or "", re.M):
            out.setdefault(mm.group(1), mm.group(2))
    if "go.sum" in m["lockfiles"]:
        for mm in re.finditer(r"^(\S+) (v\S+?)(?:/go\.mod)? h1:", _leer(os.path.join(d, "go.sum")) or "", re.M):
            out.setdefault(mm.group(1), mm.group(2))
    return out


# ------------------------------------------------------------------ outdated oficial

def ejecutor_real(cmd, cwd, timeout):
    """Devuelve (stdout, aviso|None). Inyectable en tests."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return "", f"`{' '.join(cmd)}` superó {timeout} s (¿sin red?)"
    except OSError as e:
        return "", f"`{' '.join(cmd)}` no se pudo ejecutar: {e}"
    # npm outdated devuelve exit 1 cuando HAY desactualizadas: el exit code no es error aquí
    return r.stdout, None


def parse_outdated(eco, texto):
    """{nombre: latest} a partir de la salida oficial de cada herramienta."""
    out = {}
    if not texto.strip():
        return out
    try:
        if eco == "npm":
            d = json.loads(texto)
            for k, v in (d or {}).items():
                if isinstance(v, dict) and v.get("latest"):
                    out[k] = v["latest"]
        elif eco == "composer":
            d = json.loads(texto)
            for pkg in (d or {}).get("installed") or []:
                if pkg.get("name") and pkg.get("latest"):
                    out[pkg["name"]] = str(pkg["latest"]).lstrip("v")
        elif eco in ("pip", "python"):
            for pkg in json.loads(texto) or []:
                if pkg.get("name") and pkg.get("latest_version"):
                    out[pkg["name"].lower()] = pkg["latest_version"]
        elif eco == "go":
            for mm in re.finditer(r"\{.*?\n\}", texto, re.S):
                try:
                    d = json.loads(mm.group(0))
                except ValueError:
                    continue
                upd = d.get("Update") or {}
                if d.get("Path") and upd.get("Version"):
                    out[d["Path"]] = upd["Version"]
    except ValueError:
        return {}
    return out


def outdated(m, timeout, ejecutor, avisos):
    eco = m["ecosistema"]
    if eco not in TOOLS:
        avisos.append(f"{m['manifiesto']}: sin comando «outdated» integrado para {eco} → `latest` no disponible")
        return {}
    binario, args = TOOLS[eco]
    exe = shutil.which(binario) or (shutil.which("pip3") if binario == "pip" else None)
    if not exe:
        avisos.append(f"{m['manifiesto']}: `{binario}` no está en PATH → `latest` no disponible (no se inventa)")
        return {}
    texto, aviso = ejecutor([exe, *args], m["dir"], timeout)
    if aviso:
        avisos.append(f"{m['manifiesto']}: {aviso} → `latest` no disponible")
        return {}
    res = parse_outdated(eco, texto)
    if not res and texto.strip():
        avisos.append(f"{m['manifiesto']}: salida de `{binario}` no parseable → `latest` no disponible")
    return res


# ------------------------------------------------------------------ clasificación

def semver(v):
    if not v:
        return None
    mm = _VER.search(str(v))
    if not mm:
        return None
    return tuple(int(x) if x is not None else 0 for x in mm.groups())


def salto(declarada, bloqueada, latest):
    """patch · minor · major · igual · desconocido, comparando latest con la bloqueada (si hay) o la declarada."""
    if not latest:
        return "desconocido"
    base = semver(bloqueada) or semver(declarada)
    nuevo = semver(latest)
    if base is None or nuevo is None:
        return "desconocido"
    if nuevo == base:
        return "igual"
    if nuevo < base:
        return "desconocido"
    if nuevo[0] != base[0]:
        return "major"
    if nuevo[1] != base[1]:
        return "minor"
    return "patch"


# ------------------------------------------------------------------ inventario

def inventario(root, con_outdated=True, timeout=60, ejecutor=ejecutor_real):
    avisos = []
    ms = manifiestos(root)
    ecos = []
    for m in ms:
        decl = declaradas(m, avisos)
        lock = bloqueadas(m)
        lat = outdated(m, timeout, ejecutor, avisos) if con_outdated else {}
        if not con_outdated:
            avisos.append(f"{m['manifiesto']}: `--no-outdated` → `latest` no consultado")
        deps = []
        for item in decl:
            nombre, ver, grupo = item[:3]
            extra = item[3] if len(item) > 3 else {}
            key = nombre.lower() if m["ecosistema"] in ("pip", "python") else nombre
            latest = lat.get(key) or lat.get(nombre)
            tipo = extra.get("tipo", "registro")
            deps.append({"nombre": nombre, "declarada": ver, "bloqueada": lock.get(nombre),
                         "latest": latest if tipo == "registro" else None,
                         "salto": salto(ver, lock.get(nombre), latest) if tipo == "registro" else "desconocido",
                         "grupo": grupo, "tipo": tipo, "marcador": extra.get("marcador") or None,
                         "origen": extra.get("origen")})
        ecos.append({"ecosistema": m["ecosistema"], "manifiesto": m["manifiesto"], "lockfiles": m["lockfiles"],
                     "latest_disponible": bool(lat), "dependencias": deps})
    cuenta = defaultdict(int)
    for e in ecos:
        for d in e["dependencias"]:
            cuenta[d["salto"]] += 1
    return {"ruta": os.path.abspath(root), "fecha": _dt.date.today().isoformat(),
            "manifiestos": len(ms), "dependencias": sum(len(e["dependencias"]) for e in ecos),
            "por_salto": dict(sorted(cuenta.items())), "ecosistemas": ecos, "avisos": avisos}


def md(r):
    L = [f"# Inventario de dependencias — `{r['ruta']}` ({r['fecha']})", ""]
    if not r["ecosistemas"]:
        L.append("_Sin manifiestos reconocidos (package.json, composer.json, requirements*.txt, pyproject.toml, go.mod, Gemfile, *.csproj)._")
        return "\n".join(L) + "\n"
    ps = r["por_salto"]
    L.append(f"**{r['manifiestos']} manifiesto(s) · {r['dependencias']} dependencias** · major **{ps.get('major', 0)}** · "
             f"minor {ps.get('minor', 0)} · patch {ps.get('patch', 0)} · al día {ps.get('igual', 0)} · sin `latest` {ps.get('desconocido', 0)}")
    L.append("")
    L.append("`major` = **breaking probable → leer el changelog/UPGRADING upstream antes de tocar nada**. "
             "`latest` solo viene del «outdated» oficial de cada herramienta; `—` = no consultado o no disponible (nunca se inventa).")
    for a in r["avisos"]:
        L.append(f"\n> ⚠️ {a}")
    for e in r["ecosistemas"]:
        locks = ", ".join(e["lockfiles"]) if e["lockfiles"] else "sin lockfile"
        L += ["", f"## {e['ecosistema']} — `{e['manifiesto']}` ({locks})", ""]
        if not e["dependencias"]:
            L.append("_Sin dependencias declaradas._")
            continue
        L += ["| Dependencia | Declarada | Bloqueada | Latest | Salto | Grupo | Tipo / marcador |", "|---|---|---|---|---|---|---|"]
        orden = {"major": 0, "minor": 1, "patch": 2, "desconocido": 3, "igual": 4}
        for d in sorted(e["dependencias"], key=lambda d: (orden[d["salto"]], d["nombre"])):
            marca = " ⚠️ breaking probable" if d["salto"] == "major" else ""
            tipo = d.get("tipo", "registro")
            extra = tipo if tipo == "registro" else (f"**{tipo}** `{d['origen']}`" if d.get("origen") else f"**{tipo}**")
            if d.get("marcador"):
                extra += f" · `; {d['marcador']}`"
            L.append(f"| `{d['nombre']}` | `{d['declarada']}` | {d['bloqueada'] or '—'} | {d['latest'] or '—'} | {d['salto']}{marca} | {d['grupo']} | {extra} |")
    return "\n".join(L) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    p.add_argument("ruta")
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-outdated", action="store_true", help="no ejecutar ninguna herramienta")
    p.add_argument("--timeout", type=int, default=60)
    a = p.parse_args(argv)
    if not os.path.isdir(a.ruta):
        print(f"deps-inventory: la ruta no existe o no es un directorio: {a.ruta}", file=sys.stderr)
        return 2
    r = inventario(a.ruta, con_outdated=not a.no_outdated, timeout=a.timeout)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else md(r), end="\n" if a.json else "")
    return 0


if __name__ == "__main__":
    sys.exit(main())
