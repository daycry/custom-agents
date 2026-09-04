#!/usr/bin/env python3
"""
changelog-sync.py — entradas `[Unreleased]`/`[Sin publicar]` desde los ledgers CERRADOS.

(Iniciativa superiority T-02, lección LES-012: el papeleo mecánico del release lo hace un
script, no el modelo. Aquí: el CHANGELOG se deriva del ledger, que es la fuente única del
progreso — no de la memoria de la conversación.)

Qué hace
  1. Recorre `docs/roadmap/<fecha>-<slug>/tasks.md` y toma los ledgers con `estado: completado`
     en el frontmatter (los legacy sin frontmatter se ignoran con aviso).
  2. Descarta los que YA aparecen en el CHANGELOG (busca `` `<slug>` `` en el texto) → idempotente.
  3. Por cada ledger pendiente escribe, justo bajo la cabecera Unreleased y en orden de fecha,
     una subsección `### <Categoría> — \\`<slug>\\` initiative (<fecha>)` (EN) /
     `### <Categoría> — iniciativa \\`<slug>\\` (<fecha>)` (ES) con UN bullet por tarea `T-XX`:
     título + primera frase de su Descripción + hasta 5 `Archivos` clave.
  4. Categoría por heurística sobre `descripcion:` y títulos (fix/corrige/saldar/bug → Fixed;
     cambia/retira/renombra/migra/sustituye → Changed; resto Added), sobreescribible con
     `changelog: Added|Changed|Fixed` en el frontmatter del ledger.

Uso:  changelog-sync.py [--root <repo>] [--dry-run] [--only <slug>] [--check] [--json]
Exit: 0 ok (o nada pendiente) · 1 con `--check` y entradas pendientes · 2 error de uso
      (no hay CHANGELOG.md/CHANGELOG.es.md, o `--only` sin ledger cerrado que case).

NO hace: no crea la sección de versión (eso es `scripts/release.py`), no inventa alcance, no
traduce con modelo (el bullet ES y EN salen del MISMO texto del ledger, que está en español;
afinar la redacción es trabajo humano posterior — la skill lo explica).
"""
import argparse
import json
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

LEDGER_GLOB = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")
CHANGELOGS = {  # fichero → (cabecera de la sección abierta, plantilla de subsección)
    "CHANGELOG.md": ("## [Unreleased]", "### {cat} — `{slug}` initiative ({fecha})"),
    "CHANGELOG.es.md": ("## [Sin publicar]", "### {cat} — iniciativa `{slug}` ({fecha})"),
}
CATS = ("Added", "Changed", "Fixed")
RE_FIXED = re.compile(r"\b(fix|corrig\w+|correcci[oó]n|saldar|saldad\w+|bug|regresi[oó]n)\b", re.I)
RE_CHANGED = re.compile(r"\b(cambia\w*|retira\w*|renombra\w*|migra\w*|sustituy\w*|reemplaza\w*)\b", re.I)


# --------------------------------------------------------------- lectura del ledger ----
def frontmatter(text):
    """dict del frontmatter YAML plano (clave: valor) o {} si no hay."""
    lines = text.lstrip("﻿").split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    out = {}
    for l in lines[1:]:
        if l.strip() == "---":
            break
        m = re.match(r"([A-Za-z_][\w-]*)\s*:\s*(.*)$", l)
        if m:
            out[m.group(1)] = m.group(2).split("#")[0].strip().strip('"\'')
    return out


def primera_frase(s):
    s = re.sub(r"\s+", " ", s).strip()
    # corta en el primer punto seguido de espacio+mayúscula (evita cortar «p. ej.» y versiones)
    m = re.search(r"\.(?=\s+[A-ZÁÉÍÓÚÑ¿«`])", s)
    return (s[: m.start()] if m else s).rstrip(" .") + "."


def archivos_clave(s, maximo=5):
    """Tokens entre acentos graves del campo Archivos, sin las anotaciones entre paréntesis."""
    out = []
    for tok in re.findall(r"`([^`]+)`", s or ""):
        tok = re.sub(r"\s*\([^)]*\)", "", tok).strip()
        if tok and tok not in out:
            out.append(tok)
        if len(out) >= maximo:
            break
    return out


def tareas(text):
    """[(id, titulo, descripcion, archivos)] en orden de aparición."""
    out = []
    bloques = re.split(r"\n(?=### (?:T-\d+|Fase)\b)", text)
    for b in bloques:
        m = re.match(r"### (T-\d+)\s*[—-]\s*(.+)", b)
        if not m:
            continue
        desc = re.search(r"^- \*\*Descripci[oó]n\*\*:\s*(.+)$", b, re.M)
        arch = re.search(r"^- \*\*Archivos\*\*:\s*(.+)$", b, re.M)
        out.append((m.group(1), m.group(2).strip(),
                    primera_frase(desc.group(1)) if desc else "",
                    archivos_clave(arch.group(1) if arch else "")))
    return out


def categoria(fm, tits):
    c = (fm.get("changelog") or "").strip().capitalize()
    if c in CATS:
        return c
    texto = " ".join([fm.get("descripcion", "")] + tits)
    if RE_FIXED.search(texto):
        return "Fixed"
    if RE_CHANGED.search(texto):
        return "Changed"
    return "Added"


def ledgers(root):
    """[(fecha, slug, path, frontmatter, tareas)] de los ledgers COMPLETADOS, por fecha+slug."""
    base = os.path.join(root, "docs", "roadmap")
    out, avisos = [], []
    if not os.path.isdir(base):
        return out, ["docs/roadmap/ no existe: nada que sincronizar"]
    for d in sorted(os.listdir(base)):
        m = LEDGER_GLOB.match(d)
        p = os.path.join(base, d, "tasks.md")
        if not m or not os.path.isfile(p):
            continue
        try:
            text = open(p, encoding="utf-8-sig").read()
        except OSError as e:
            avisos.append(f"{d}: no se puede leer ({e})")
            continue
        fm = frontmatter(text)
        if not fm:
            avisos.append(f"{d}: ledger sin frontmatter (legacy) — se ignora")
            continue
        if fm.get("estado") != "completado":
            continue
        ts = tareas(text)
        if not ts:
            avisos.append(f"{d}: completado pero sin tareas T-XX reconocibles — se ignora")
            continue
        out.append((m.group(1), m.group(2), p, fm, ts))
    return out, avisos


# ------------------------------------------------------------------ render / escritura ----
def bullets(ts):
    out = []
    for tid, tit, desc, arch in ts:
        linea = f"- **{tid} — {tit}**"
        if desc:
            linea += f" {desc}"
        if arch:
            linea += " (" + ", ".join(f"`{a}`" for a in arch) + ")"
        out.append(linea)
    return out


def seccion(plantilla, cat, slug, fecha, ts):
    return "\n".join([plantilla.format(cat=cat, slug=slug, fecha=fecha), ""] + bullets(ts) + [""])


def pendientes(root, only=None):
    """[(fecha, slug, cat, ts)] pendientes en AL MENOS un CHANGELOG + avisos."""
    regs, avisos = ledgers(root)
    textos = {}
    for fn in CHANGELOGS:
        p = os.path.join(root, fn)
        if not os.path.isfile(p):
            return None, avisos + [f"falta {fn}"], None
        textos[fn] = open(p, encoding="utf-8").read()
    out = []
    for fecha, slug, _p, fm, ts in regs:
        if only and slug != only:
            continue
        falta = [fn for fn, t in textos.items() if f"`{slug}`" not in t]
        if falta:
            out.append((fecha, slug, categoria(fm, [t[1] for t in ts]), ts, falta))
    return out, avisos, textos


def insertar(text, cabecera, bloque):
    """Inserta el bloque justo debajo de la cabecera Unreleased (y su línea en blanco)."""
    i = text.index(cabecera) + len(cabecera)
    resto = text[i:]
    j = len(resto) - len(resto.lstrip("\n"))
    return text[:i] + "\n" * max(j, 2) + bloque + resto[j:]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Entradas [Unreleased] desde los ledgers cerrados.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--json", action="store_true", dest="as_json")
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    pend, avisos, textos = pendientes(root, a.only)
    if pend is None:
        for v in avisos:
            print(f"changelog-sync: {v}", file=sys.stderr)
        return 2
    if a.only and not pend and not any(True for _ in ()):
        # --only con un slug que no existe entre los cerrados (o ya sincronizado): distíngelo
        regs, _ = ledgers(root)
        if a.only not in [s for _f, s, *_ in regs]:
            print(f"changelog-sync: no hay ledger CERRADO con slug «{a.only}»", file=sys.stderr)
            return 2
    res = {"root": root, "pendientes": [{"slug": s, "fecha": f, "categoria": c,
                                         "tareas": len(ts), "ficheros": fl}
                                        for f, s, c, ts, fl in pend],
           "avisos": avisos, "escrito": []}
    if a.check:
        if a.as_json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            for v in avisos:
                print(f"⚠️  {v}")
            if pend:
                print("changelog-sync --check: entradas PENDIENTES en el CHANGELOG:")
                for f, s, c, ts, fl in pend:
                    print(f"  · {s} ({f}) — {c}, {len(ts)} tarea(s) → falta en {', '.join(fl)}")
                print("Ejecuta `changelog-sync.py` (sin --check) para generarlas.")
            else:
                print("changelog-sync --check: sin entradas pendientes ✅")
        return 1 if pend else 0
    for fn, (cabecera, plantilla) in CHANGELOGS.items():
        bloques = [seccion(plantilla, c, s, f, ts) for f, s, c, ts, fl in pend if fn in fl]
        if not bloques:
            continue
        nuevo = textos[fn]
        # se insertan en orden de fecha ASCENDENTE justo bajo la cabecera: cada inserción
        # empuja a la anterior hacia abajo, así la iniciativa MÁS RECIENTE acaba arriba.
        for b in bloques:
            nuevo = insertar(nuevo, cabecera, b + "\n")
        if a.dry_run:
            res["escrito"].append({"fichero": fn, "secciones": len(bloques), "dry_run": True})
            if not a.as_json:
                print(f"── {fn} (--dry-run, NO escrito):")
                print("\n".join(b.rstrip() for b in bloques))
        else:
            with open(os.path.join(root, fn), "w", encoding="utf-8", newline="") as fh:
                fh.write(nuevo)
            res["escrito"].append({"fichero": fn, "secciones": len(bloques)})
    if a.as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for v in avisos:
            print(f"⚠️  {v}")
        if not pend:
            print("changelog-sync: sin entradas pendientes ✅ (idempotente)")
        elif not a.dry_run:
            print(f"changelog-sync: {len(pend)} iniciativa(s) añadidas a "
                  f"{', '.join(sorted(CHANGELOGS))} — revisa y afina el texto antes del release.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
