#!/usr/bin/env python3
"""
confluence-scope.py — verificador + staging DETERMINISTA de la política de
publicación en Confluence (skill `confluence-publish`). Es la **fuente de
verdad** del alcance: la skill lo invoca en vez de reinterpretar los
patrones `include`/`exclude` por su cuenta, para que la semántica de glob
nunca diverja entre "lo que dice el verificador" y "lo que de verdad se
publica" (riesgo señalado en `evaluation.md`).

Subcomandos (exactamente uno por invocación):
  --check   Verifica las invariantes NO NEGOCIABLES de la config resuelta
            (hoy: `docs/security-scan/**` debe quedar excluido). Exit 0 si
            no hay violaciones; exit 1 + mensaje que NOMBRA la invariante
            violada en caso contrario.
  --status  Recorre `docs/` aplicando `include`/`exclude`, cruza el
            resultado con el manifiesto `.claude/confluence-state.json`
            (si existe) y clasifica cada `.md` en:
              en alcance → sincronizado | desactualizado | pendiente
              excluido   → con el patrón que lo excluyó
            Termina con exit 0 si el análisis se completó (el estado de los
            ficheros NO afecta al exit code — para eso está `--check`).
  --stage   Regenera `docs/confluence/` DESDE CERO: copia byte a byte de los
            ficheros en alcance + un fichero de aviso `_STAGING-LEEME.md`
            (nombre reservado, NUNCA colisiona con un `README.md` real:
            queda excluido del alcance en cualquier carpeta, y su mapeo
            inverso es siempre huérfano). Idempotente: dos ejecuciones
            seguidas sin cambios en `docs/` producen el mismo árbol. La
            propia carpeta `docs/confluence/**` se autoexcluye SIEMPRE
            (aunque la config no lo declare) para que un `--stage` no se
            anide dentro del anterior.
  --map RUTA
            Resuelve el mapeo INVERSO staged → canónico de una ruta bajo
            `docs/confluence/` (admite ruta absoluta o relativa al
            staging). Es aritmética pura de rutas (la copia es 1:1 salvo el
            prefijo `docs/confluence/`), así que no depende de haber
            corrido `--stage` antes. Exit 0 + ruta canónica por stdout si
            el fichero canónico existe; exit 1 si es una página huérfana
            (sin correspondencia en `docs/`) — nunca escribas en ese caso.

Uso:
  python3 confluence-scope.py --check  [--root DIR] [--config RUTA]
  python3 confluence-scope.py --status [--root DIR] [--config RUTA] [--state RUTA]
  python3 confluence-scope.py --stage  [--root DIR] [--config RUTA] [--out DIR]
  python3 confluence-scope.py --map docs/confluence/README.md [--root DIR] [--out DIR]

Resolución de rutas relativas (dos familias, documentado explícitamente
tras la revisión adversarial — reproducido: `--root demo --out demo/docs`
crea `demo/demo/docs` en silencio si se asume la familia equivocada):
  - `--docs` y `--out`: relativos a `--root` (son ubicaciones DENTRO del
    árbol del proyecto: "el directorio de docs de este proyecto", "la
    salida del staging de este proyecto"). Un `--out` que ya incluya el
    propio `--root` como prefijo se ANIDA (pásalo relativo AL PROYECTO,
    no a `--root` otra vez).
  - `--config` y `--state`: relativos al **directorio de trabajo actual**
    (son punteros a un fichero explícito que puede vivir fuera del árbol
    del proyecto, p. ej. un fixture de test) — comportamiento estándar de
    `Path`, sin resolución especial.
  Con cualquier ruta relativa, si tienes dudas usa una ruta absoluta.

Sin dependencias externas (solo stdlib). Localiza sus propios assets con
`Path(__file__).resolve()` — nunca rutas absolutas del repo (regla de
scripts del plugin).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ASSET = SCRIPT_DIR.parent / "assets" / "confluence.example.json"

# Exclusión NO negociable, SIEMPRE activa aunque falte de la config del
# proyecto: la carpeta staged se autoexcluye (D5, spec confluence-policy).
ALWAYS_EXCLUDE = ["docs/confluence/**"]

# Nombre RESERVADO del fichero de aviso del staging. Nunca es un fichero
# canónico real: se excluye del alcance en CUALQUIER carpeta bajo docs/ (no
# solo dentro de la carpeta staged), así que jamás colisiona con un
# `README.md` de verdad ni lo pisa (gap C1, revisión adversarial). Su mapeo
# inverso es siempre huérfano (no existe `docs/<...>/_STAGING-LEEME.md`
# canónico).
STAGE_MARKER_NAME = "_STAGING-LEEME.md"

# Fichero-sonda para comprobar la invariante de nemesis sin depender de que
# exista contenido real bajo docs/security-scan/ en el proyecto.
SECURITY_SCAN_PROBE = "docs/security-scan/__confluence_scope_probe__.md"

STAGE_README_TEMPLATE = """# {marker} — carpeta GENERADA, no editable

**No edites nada dentro de esta carpeta a mano.** Se REGENERA POR COMPLETO
en cada ejecución de `confluence-scope.py --stage`; cualquier cambio manual
se pierde en la siguiente regeneración.

Es la materialización exacta de la política de publicación en Confluence
(`skills/confluence-publish/SKILL.md`, sección "qué sube y qué no"): copia
byte a byte de los `.md` de `docs/` que SÍ se publican, con la misma
estructura de carpetas (sin el prefijo `docs/`).

- Comando: `python3 skills/confluence-publish/scripts/confluence-scope.py --stage`
- Ficheros en este staging: {n}

Este fichero se llama `{marker}` (no `README.md`) A PROPÓSITO: así nunca
pisa la copia real de un `docs/README.md` canónico ni ningún otro README
del árbol. Los agentes siguen escribiendo TODO (ADRs, arquitectura,
roadmap, gotchas) en sus sitios canónicos de `docs/`; esta carpeta es solo
la vista derivada de "qué sube", nunca una entrada. `confluence-pull` nunca
escribe aquí: siempre resuelve el fichero canónico con el mapeo inverso
(`--map`).
"""


def glob_to_regex(pattern):
    """Traduce un patrón glob con '**' de directorios (semántica de
    `glob.glob(..., recursive=True)`: '**/x' también matchea 'x', cero
    directorios) a una regex ANCLADA. No depende del módulo `glob` para
    poder matchear contra rutas ya calculadas (no contra el filesystem)."""
    pattern = pattern.replace("\\", "/")
    out = []
    i, n = 0, len(pattern)
    while i < n:
        if pattern[i:i + 3] == "**/":
            out.append("(?:.*/)?")
            i += 3
        elif pattern[i:i + 2] == "**":
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def glob_match(pattern, path):
    return glob_to_regex(pattern).match(path) is not None


class ConfigError(Exception):
    """Config de proyecto pasada EXPLÍCITAMENTE con --config que no existe o
    está corrupta (gap I3, revisión adversarial). A diferencia de la
    ausencia de config (que degrada a defaults sin bloquear), pedir una
    ruta concreta y que se ignore en silencio validaría una política que
    nadie ha comprobado de verdad: aquí no hay degradación posible."""


def load_policy(root, config_path=None):
    """Devuelve (dict `publish`, descripción de la fuente). Degrada sin
    bloquear SOLO cuando no se pide una config explícita: sin `--config`,
    ausencia/rotura de `.claude/confluence.json` cae a los defaults del
    propio paquete (`assets/confluence.example.json`). Con `--config`
    explícito, un fichero inexistente o corrupto es un error de uso
    (`ConfigError`), no una degradación silenciosa (gap I3)."""
    if config_path:
        c = Path(config_path)
        if not c.is_file():
            raise ConfigError(f"--config apunta a un fichero que no existe: {c}")
        try:
            data = json.loads(c.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise ConfigError(f"--config {c} no es JSON válido: {e}")
        publish = data.get("publish")
        if not publish:
            raise ConfigError(f"--config {c} no tiene bloque `publish`")
        return publish, f"config de proyecto ({c})"

    default_project_config = Path(root) / ".claude" / "confluence.json"
    if default_project_config.is_file():
        try:
            data = json.loads(default_project_config.read_text(encoding="utf-8"))
            publish = data.get("publish")
            if publish:
                return publish, f"config de proyecto ({default_project_config})"
        except (json.JSONDecodeError, OSError):
            pass  # config rota SIN pedirla explícitamente: cae a defaults, nunca bloquea
    try:
        data = json.loads(DEFAULT_ASSET.read_text(encoding="utf-8"))
        return data.get("publish", {"include": ["**/*.md"], "exclude": []}), \
            f"defaults ({DEFAULT_ASSET})"
    except (json.JSONDecodeError, OSError):
        return {"include": ["**/*.md"], "exclude": []}, "defaults embebidos (sin fichero legible)"


def check_invariants(publish):
    excludes = list(publish.get("exclude", [])) + ALWAYS_EXCLUDE
    violations = []
    if not any(glob_match(p, SECURITY_SCAN_PROBE) for p in excludes):
        violations.append(
            "INVARIANTE VIOLADA: docs/security-scan/** no está cubierto por "
            "`exclude` — el escáner de nemesis quedaría publicable en Confluence.")
    return violations


def iter_md_files(docs_root):
    for dirpath, dirnames, filenames in os.walk(docs_root):
        dirnames.sort()
        for fn in sorted(filenames):
            if fn.endswith(".md"):
                yield Path(dirpath) / fn


def rel_from_root(path, root):
    return str(Path(path).resolve().relative_to(Path(root).resolve())).replace(os.sep, "/")


def resolve_out_dir(root, docs_dirname, out):
    """Resuelve el directorio de salida del staging. `out` relativo se
    ancla a `root` (NO al cwd) — es una ubicación DENTRO del proyecto,
    igual que `--docs`; distinto de `--config`/`--state`, que son punteros
    a un fichero explícito y se resuelven relativos al cwd (documentado en
    el docstring del módulo tras la revisión adversarial: `--root demo
    --out demo/docs` anida en `demo/demo/docs` si se pasa ya prefijado con
    `--root` en vez de relativo al proyecto)."""
    if out:
        p = Path(out)
        return p if p.is_absolute() else Path(root) / p
    return Path(root) / docs_dirname / "confluence"


def always_exclude_for(root, out_dir):
    """Exclusión NO negociable de la carpeta de salida del staging,
    derivada del `--out`/`--docs` EFECTIVOS (gap I2, revisión adversarial)
    — nunca cableada al literal `docs/confluence/**`: un `--out` no
    default no quedaba excluido y la segunda ejecución de `--stage`
    intentaba recopiar ficheros recién borrados por la primera. Si
    `out_dir` cae fuera de `root` (nada que excluir de un recorrido de
    `docs/`), no añade nada."""
    try:
        rel = out_dir.resolve().relative_to(Path(root).resolve())
    except ValueError:
        return []
    return [str(rel).replace(os.sep, "/") + "/**"]


def resolve_scope(root, publish, docs_dirname="docs", out_dir=None):
    """Devuelve (en_alcance, excluidos): listas ordenadas de rutas
    'docs/...' relativas a `root`. `excluidos` es lista de tuplas
    (ruta, patrón_que_excluyó). `out_dir` (si se da) se autoexcluye
    SIEMPRE, derivado dinámicamente (gap I2) — no del literal por defecto.
    El nombre reservado `STAGE_MARKER_NAME` se excluye en CUALQUIER
    carpeta, no solo dentro de `out_dir` (gap C1: nunca puede colisionar
    con un `README.md` real)."""
    if out_dir is None:
        out_dir = resolve_out_dir(root, docs_dirname, None)
    docs_root = Path(root) / docs_dirname
    includes = publish.get("include", ["**/*.md"])
    excludes = list(publish.get("exclude", [])) + ALWAYS_EXCLUDE + always_exclude_for(root, out_dir)
    en_alcance, excluidos = [], []
    if not docs_root.is_dir():
        return en_alcance, excluidos
    for f in iter_md_files(docs_root):
        rel = rel_from_root(f, root)
        if f.name == STAGE_MARKER_NAME:
            excluidos.append((rel, f"nombre reservado ({STAGE_MARKER_NAME})"))
            continue
        included = any(glob_match(p, rel) for p in includes)
        excl_pat = next((p for p in excludes if glob_match(p, rel)), None)
        if included and not excl_pat:
            en_alcance.append(rel)
        else:
            excluidos.append((rel, excl_pat or "(ningún patrón de `include` matchea)"))
    return sorted(en_alcance), sorted(excluidos)


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_manifest(root, state_path=None):
    p = Path(state_path) if state_path else Path(root) / ".claude" / "confluence-state.json"
    if not p.is_file():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def classify_sync(en_alcance, root, manifest):
    """rel_path -> 'sincronizado' | 'desactualizado' | 'pendiente'."""
    out = {}
    for rel in en_alcance:
        entry = manifest.get(rel)
        if entry is None:
            out[rel] = "pendiente"
            continue
        try:
            actual = sha256_of(Path(root) / rel)
        except OSError:
            out[rel] = "pendiente"
            continue
        out[rel] = "sincronizado" if actual == entry.get("hash") else "desactualizado"
    return out


def cmd_check(args):
    publish, fuente = load_policy(args.root, args.config)
    violations = check_invariants(publish)
    print(f"confluence-scope --check: política resuelta desde {fuente}")
    if violations:
        for v in violations:
            print(f"❌ {v}")
        print(f"confluence-scope --check: {len(violations)} invariante(s) violada(s)")
        return 1
    print("confluence-scope --check: OK (0 invariantes violadas)")
    return 0


def cmd_status(args):
    publish, fuente = load_policy(args.root, args.config)
    print(f"confluence-scope --status: política resuelta desde {fuente}")
    out_dir = resolve_out_dir(args.root, args.docs, args.out)
    excludes = list(publish.get("exclude", [])) + ALWAYS_EXCLUDE + always_exclude_for(args.root, out_dir)
    print("\nPatrones de exclusión activos:")
    for p in excludes:
        print(f"  - {p}")

    docs_root = Path(args.root) / args.docs
    if not docs_root.is_dir():
        print(f"\n(no existe {args.docs}/ en {args.root}: nada más que analizar)")
        return 0

    en_alcance, excluidos = resolve_scope(args.root, publish, args.docs, out_dir)
    manifest = load_manifest(args.root, args.state)
    sync = classify_sync(en_alcance, args.root, manifest)

    print(f"\nEn alcance ({len(en_alcance)}):")
    for rel in en_alcance:
        print(f"  [{sync[rel]}] {rel}")
    print(f"\nExcluidos ({len(excluidos)}):")
    for rel, pat in excluidos:
        print(f"  [excluido: {pat}] {rel}")

    counts = {}
    for v in sync.values():
        counts[v] = counts.get(v, 0) + 1
    print(f"\nResumen: {len(en_alcance)} en alcance "
          f"(sincronizado={counts.get('sincronizado', 0)} · "
          f"desactualizado={counts.get('desactualizado', 0)} · "
          f"pendiente={counts.get('pendiente', 0)}) · "
          f"{len(excluidos)} excluidos")
    return 0


class UnsafeStageTarget(Exception):
    """`--out` apunta a un directorio que no parece un staging propio: no se
    borra (gap C2, revisión adversarial). El llamador debe tratarlo como
    error de uso."""


def assert_safe_stage_target(out_dir):
    """Salvaguarda ANTES de borrar nada: `out_dir` tiene que ser uno de
    - no existe todavía,
    - existe y está vacío,
    - existe y contiene el marcador `STAGE_MARKER_NAME` (es reconocible
      como un staging generado por una ejecución anterior de este script).
    Cualquier otro caso (un directorio ajeno con contenido real, p. ej.
    `docs/` entero) se rechaza SIN tocar nada."""
    if not out_dir.exists():
        return
    if not out_dir.is_dir():
        raise UnsafeStageTarget(f"--out {out_dir} existe y NO es un directorio: no se toca")
    entries = list(out_dir.iterdir())
    if not entries:
        return
    if (out_dir / STAGE_MARKER_NAME).is_file():
        return
    raise UnsafeStageTarget(
        f"--out {out_dir} existe, NO está vacío y no contiene el marcador "
        f"de staging ({STAGE_MARKER_NAME}) — parece un directorio real del "
        f"proyecto. Por seguridad, --stage rehúsa borrarlo. Si de verdad es "
        f"un staging antiguo de otra herramienta, vacíalo a mano primero.")


def cmd_stage(args):
    publish, fuente = load_policy(args.root, args.config)
    out_dir = resolve_out_dir(args.root, args.docs, args.out)
    assert_safe_stage_target(out_dir)  # gap C2: nunca borres un directorio ajeno

    en_alcance, _ = resolve_scope(args.root, publish, args.docs, out_dir)  # gap I2: out_dir dinámico

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for rel in en_alcance:
        rel_in_docs = str(Path(rel).relative_to(args.docs))  # quita el prefijo 'docs/'
        src = Path(args.root) / rel
        dst = out_dir / rel_in_docs
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)  # byte a byte: NUNCA se sobreescribe con la plantilla (gap C1)

    marker = out_dir / STAGE_MARKER_NAME
    assert not marker.exists(), (
        f"invariante rota: {STAGE_MARKER_NAME} ya existía tras copiar el alcance "
        f"(debería estar siempre excluido por `resolve_scope`)")
    marker.write_text(
        STAGE_README_TEMPLATE.format(marker=STAGE_MARKER_NAME, n=len(en_alcance)),
        encoding="utf-8")

    print(f"confluence-scope --stage: política resuelta desde {fuente}")
    print(f"confluence-scope --stage: {len(en_alcance)} fichero(s) copiado(s) a {out_dir}")
    return 0


def staged_to_canonical(staged_path, root, docs_dirname="docs", out_dir=None):
    """Mapeo inverso staged → canónico. Es aritmética PURA de rutas (la
    copia de `--stage` es 1:1 salvo el prefijo `docs/confluence/`), así que
    no requiere haber ejecutado `--stage` antes. Devuelve la ruta canónica
    relativa a `root` ('docs/...') o `None` si es una página huérfana
    (ruta vacía, no corresponde a ningún fichero real bajo `docs/`, o
    `out_dir`/`staged_path` no anida dentro de `root` — gap M1: nunca deja
    escapar `ValueError`). Resuelve `out_dir` con `resolve_out_dir`
    (gap I2): un `--out` relativo se ancla a `root`, igual que en
    `cmd_stage`, en vez de resolverse contra el cwd."""
    if not str(staged_path).strip():  # gap I4: cadena vacía es huérfana, no "sin especificar"
        return None
    out_dir = resolve_out_dir(root, docs_dirname, out_dir)
    p = Path(staged_path)
    try:
        if p.is_absolute():
            rel = p.resolve().relative_to(out_dir.resolve())
        else:
            s = str(p).replace(os.sep, "/")
            prefix = str(out_dir.resolve().relative_to(Path(root).resolve())).replace(os.sep, "/")
            rel = Path(s[len(prefix) + 1:]) if s.startswith(prefix + "/") else Path(s)
    except ValueError:
        return None  # gap M1: out_dir fuera de root (o staged_path fuera de out_dir) -> huérfana
    if rel == Path(STAGE_MARKER_NAME):
        return None  # el propio marcador nunca tiene canónico (gap C1)
    canonical = Path(root) / docs_dirname / rel
    if not canonical.is_file():
        return None
    return str(Path(docs_dirname) / rel).replace(os.sep, "/")


def cmd_map(args):
    if not args.map.strip():  # gap I4: exit != 0, no "exit 0 sin salida"
        print("confluence-scope --map: ruta vacía — indica una ruta bajo el staging")
        return 2
    canonical = staged_to_canonical(args.map, args.root, args.docs, args.out)
    if canonical is None:
        print(f"confluence-scope --map: ruta huérfana, sin fichero canónico "
              f"correspondiente a {args.map!r} — no escribas nada")
        return 1
    print(canonical)
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="verifica invariantes no negociables")
    g.add_argument("--status", action="store_true", help="informe de alcance y sincronización")
    g.add_argument("--stage", action="store_true", help="regenera docs/confluence/")
    g.add_argument("--map", metavar="RUTA_STAGED", help="mapeo inverso staged -> canónico")
    ap.add_argument("--root", default=".", help="raíz del proyecto (default: cwd)")
    ap.add_argument("--config", help="ruta explícita a confluence.json (override; relativa al cwd, NO a --root)")
    ap.add_argument("--state", help="ruta explícita a confluence-state.json (override; relativa al cwd, NO a --root)")
    ap.add_argument("--docs", default="docs", help="nombre del directorio de docs, relativo a --root (default: docs)")
    ap.add_argument("--out", help="directorio de salida del staging, relativo a --root si no es absoluto "
                                  "(default: <root>/<docs>/confluence) — NO relativo al cwd")
    args = ap.parse_args()

    try:
        if args.check:
            sys.exit(cmd_check(args))
        if args.status:
            sys.exit(cmd_status(args))
        if args.stage:
            sys.exit(cmd_stage(args))
        if args.map is not None:  # gap I4: "" es un valor válido a rechazar DENTRO
            sys.exit(cmd_map(args))  # de cmd_map, no un "no se pasó" que se salte el dispatch
    except UnsafeStageTarget as e:
        print(f"confluence-scope: {e}")
        sys.exit(2)
    except ConfigError as e:
        print(f"confluence-scope: config inválida — {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
