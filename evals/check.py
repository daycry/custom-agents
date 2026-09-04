#!/usr/bin/env python3
"""
check.py — validación ESTÁTICA de la suite de evals (`evals/cases/*.json`). Corre en CI; no
necesita `claude` ni red. Es la mitad determinista de la fiabilidad de activación: `run.py`
mide si la pieza se dispara; este script garantiza que la suite exista, sea coherente y siga
atada a las `description` reales del repo.

Comprueba (exit 1 si algo falla, 0 si todo pasa):
  1. Esquema: cada fichero es JSON con `target` (`skill:<n>` | `command:<n>` | `agent:<n>`) y
     `cases` no vacío; cada caso tiene `id` (`^[a-z0-9][a-z0-9-]*$`), `prompt` (texto no vacío),
     `expect.activates` (bool) y, opcionales, `expect.artifacts` / `expect.mentions` /
     `expect.must_not` (listas de cadenas), `expect.redirect` (`kind:name` de otra pieza),
     `trigger` (`literal` | `parafrasis`, solo en positivos) y `notes`.
  2. Nombre de fichero = target con `:` → `-` (`skill:quick-implement` → `skill-quick-implement.json`).
  3. Cobertura: TODA pieza del repo (skills/*/SKILL.md, commands/*.md, agents/*.md) tiene su fichero
     con ≥ 2 positivos (prompts distintos entre sí) + ≥ 1 negativo.
  4. Disparador literal: ≥ 1 positivo `trigger: literal` cuyo prompt contiene una frase presente en la
     `description` REAL del target — una frase entrecomillada ("…"/«…») de la description o una
     ventana de 4 palabras consecutivas de ella (comparación normalizada: minúsculas, sin acentos,
     sin markdown). Así, si la description cambia, el caso rompe y obliga a mantener ambas.
  5. Ids únicos en TODA la suite.
  6. Sin datos corporativos (repo público): correos (salvo example.*), hosts `*.atlassian.net`, URLs
     (salvo localhost/example/127.0.0.1), claves Jira reales (`ABC-123`; se permite `PROJ-` y los
     prefijos del propio método: T-, E2E-, M-, CA-, CWE-, ADR-, GOT-, LES-, API-, A11Y-).
  7. `redirect` apunta a una pieza existente; un negativo no puede tener `trigger`.

Uso:  python3 evals/check.py [--root DIR] [--json]
"""
import argparse
import json
import os
import re
import sys
import unicodedata

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = ("skill", "command", "agent")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
TRIGGERS = {"literal", "parafrasis"}
MIN_POS, MIN_NEG, WINDOW = 2, 1, 4

# --- regla anti datos corporativos (repo público) --------------------------------------
_JIRA_OK = ("PROJ", "T", "E2E", "M", "CA", "CWE", "ADR", "GOT", "LES", "API", "A11Y", "GWT", "OWASP", "ISO")
CORPORATE_RES = [
    ("correo", re.compile(r"[\w.+-]+@(?!example\.)[\w-]+\.[a-z]{2,}", re.I)),
    ("host atlassian", re.compile(r"[\w-]+\.atlassian\.net", re.I)),
    ("url", re.compile(r"https?://(?!localhost|127\.0\.0\.1|example\.|[\w.-]*\.example\.|[\w.-]*\.test\b)[\w.-]+", re.I)),
    ("clave jira", re.compile(r"\b(?!(?:%s)-)[A-Z][A-Z0-9]{1,9}-\d+\b" % "|".join(_JIRA_OK))),
]


def normaliza(texto):
    """minúsculas, sin acentos, sin markdown (`**`, backticks), espacios colapsados."""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[`*_>]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def frases_de(description):
    """Frases candidatas del disparador literal: entrecomilladas + ventanas de WINDOW palabras."""
    frases = set()
    for m in re.finditer(r"[\"“«]([^\"”»]{3,})[\"”»]", description):
        frases.add(normaliza(m.group(1)))
    palabras = re.findall(r"[a-z0-9áéíóúñü/.-]+", normaliza(description))
    palabras = [p.strip(".") for p in palabras if p.strip(".")]
    for i in range(0, max(0, len(palabras) - WINDOW + 1)):
        frases.add(" ".join(palabras[i:i + WINDOW]))
    return {f for f in frases if f}


def contiene_frase(prompt, frases):
    p = " " + normaliza(prompt) + " "
    for f in sorted(frases, key=len, reverse=True):
        if (" " + f + " ") in p or (len(f) > 12 and f in p):
            return f
    return None


# --- piezas del repo ------------------------------------------------------------------

def _frontmatter(path):
    text = open(path, encoding="utf-8-sig").read()
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm, out, key = text[3:end], {}, None
    for raw in fm.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] not in " \t" and ":" in raw:
            key, val = raw.split(":", 1)
            key, val = key.strip(), val.strip()
            out[key] = "" if val in (">", "|", ">-", "|-") else val
        elif key and raw[0] in " \t":
            out[key] = (out.get(key, "") + " " + raw.strip()).strip()
    return out


def piezas(root):
    """{'skill:x': description, 'command:y': …, 'agent:z': …} leyendo los frontmatters reales."""
    out = {}
    sk = os.path.join(root, "skills")
    if os.path.isdir(sk):
        for d in sorted(os.listdir(sk)):
            p = os.path.join(sk, d, "SKILL.md")
            if os.path.isfile(p):
                out[f"skill:{d}"] = _frontmatter(p).get("description", "")
    for kind, sub in (("command", "commands"), ("agent", "agents")):
        dd = os.path.join(root, sub)
        if os.path.isdir(dd):
            for fn in sorted(os.listdir(dd)):
                if fn.endswith(".md"):
                    out[f"{kind}:{fn[:-3]}"] = _frontmatter(os.path.join(dd, fn)).get("description", "")
    return out


def nombre_fichero(target):
    return target.replace(":", "-") + ".json"


# --- validación -----------------------------------------------------------------------

def cargar_casos(cases_dir):
    """[(fichero, dict|None, error|None)] de todos los .json de evals/cases/."""
    out = []
    if not os.path.isdir(cases_dir):
        return out
    for fn in sorted(os.listdir(cases_dir)):
        if not fn.endswith(".json"):
            continue
        p = os.path.join(cases_dir, fn)
        try:
            out.append((fn, json.load(open(p, encoding="utf-8")), None))
        except (ValueError, UnicodeDecodeError) as e:
            out.append((fn, None, f"JSON inválido: {e}"))
    return out


def check(root):
    errores, stats = [], {"ficheros": 0, "casos": 0, "positivos": 0, "negativos": 0, "targets": 0}
    cases_dir = os.path.join(root, "evals", "cases")
    if not os.path.isdir(cases_dir):
        return [f"no existe {cases_dir}"], stats
    repo = piezas(root)
    stats["targets"] = len(repo)
    ids, cubiertos = {}, {}

    for fn, data, err in cargar_casos(cases_dir):
        stats["ficheros"] += 1
        if err:
            errores.append(f"{fn}: {err}")
            continue
        if not isinstance(data, dict):
            errores.append(f"{fn}: la raíz debe ser un objeto")
            continue
        target = data.get("target")
        if not isinstance(target, str) or ":" not in target or target.split(":", 1)[0] not in KINDS:
            errores.append(f"{fn}: `target` inválido {target!r} (esperado skill:|command:|agent: + nombre)")
            continue
        if nombre_fichero(target) != fn:
            errores.append(f"{fn}: el nombre del fichero debe ser `{nombre_fichero(target)}` (target {target})")
        if target not in repo:
            errores.append(f"{fn}: el target `{target}` no existe en el repo")
        casos = data.get("cases")
        if not isinstance(casos, list) or not casos:
            errores.append(f"{fn}: `cases` debe ser una lista no vacía")
            continue
        pos, neg, prompts_pos, literal_ok = 0, 0, set(), False
        frases = frases_de(repo.get(target, ""))
        for i, c in enumerate(casos):
            ref = f"{fn}#{i}"
            if not isinstance(c, dict):
                errores.append(f"{ref}: cada caso debe ser un objeto")
                continue
            cid = c.get("id")
            if not isinstance(cid, str) or not ID_RE.match(cid):
                errores.append(f"{ref}: `id` inválido {cid!r}")
            elif cid in ids:
                errores.append(f"{ref}: id duplicado `{cid}` (ya en {ids[cid]})")
            else:
                ids[cid] = fn
            prompt = c.get("prompt")
            if not isinstance(prompt, str) or not prompt.strip():
                errores.append(f"{ref}: `prompt` vacío")
                prompt = ""
            exp = c.get("expect")
            if not isinstance(exp, dict) or not isinstance(exp.get("activates"), bool):
                errores.append(f"{ref}: `expect.activates` debe ser bool")
                continue
            for k in ("artifacts", "mentions", "must_not"):
                v = exp.get(k, [])
                if not isinstance(v, list) or not all(isinstance(x, str) and x for x in v):
                    errores.append(f"{ref}: `expect.{k}` debe ser lista de cadenas")
            extra = set(exp) - {"activates", "artifacts", "mentions", "must_not", "redirect"}
            if extra:
                errores.append(f"{ref}: claves desconocidas en expect: {sorted(extra)}")
            red = exp.get("redirect")
            if red is not None and red not in repo:
                errores.append(f"{ref}: `expect.redirect` `{red}` no es una pieza del repo")
            trig = c.get("trigger")
            stats["casos"] += 1
            if exp["activates"]:
                pos += 1
                stats["positivos"] += 1
                if trig not in TRIGGERS:
                    errores.append(f"{ref}: positivo sin `trigger` válido ({sorted(TRIGGERS)})")
                if normaliza(prompt) in prompts_pos:
                    errores.append(f"{ref}: prompt positivo repetido")
                prompts_pos.add(normaliza(prompt))
                if trig == "literal":
                    if contiene_frase(prompt, frases):
                        literal_ok = True
                    else:
                        errores.append(f"{ref}: `trigger: literal` pero el prompt no contiene ninguna frase "
                                       f"de la description de `{target}` (frase entrecomillada o {WINDOW} palabras seguidas)")
            else:
                neg += 1
                stats["negativos"] += 1
                if trig is not None:
                    errores.append(f"{ref}: un negativo no lleva `trigger`")
            listas = [x for k in ("mentions", "must_not", "artifacts")
                      for x in (exp.get(k, []) if isinstance(exp.get(k, []), list) else []) if isinstance(x, str)]
            blob = " ".join([prompt, str(c.get("notes", ""))] + listas)
            for etiqueta, rx in CORPORATE_RES:
                m = rx.search(blob)
                if m:
                    errores.append(f"{ref}: posible dato corporativo ({etiqueta}): `{m.group(0)}`")
        if pos < MIN_POS:
            errores.append(f"{fn}: {pos} positivos (mínimo {MIN_POS})")
        if neg < MIN_NEG:
            errores.append(f"{fn}: {neg} negativos (mínimo {MIN_NEG})")
        if pos and not literal_ok and target in repo:
            errores.append(f"{fn}: ningún positivo `trigger: literal` casa con la description de `{target}`")
        cubiertos[target] = True

    for target in sorted(repo):
        if target not in cubiertos:
            errores.append(f"cobertura: `{target}` no tiene fichero evals/cases/{nombre_fichero(target)}")
    return errores, stats


def main(argv=None):
    ap = argparse.ArgumentParser(description="validación estática de evals/cases/*.json")
    ap.add_argument("--root", default=os.path.dirname(HERE))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    errores, stats = check(os.path.abspath(args.root))
    if args.json:
        print(json.dumps({"ok": not errores, "errores": errores, **stats}, ensure_ascii=False))
    else:
        for e in errores:
            print(f"❌ {e}")
        print(f"evals/check: {stats['ficheros']} ficheros · {stats['casos']} casos "
              f"({stats['positivos']} positivos, {stats['negativos']} negativos) · "
              f"{stats['targets']} piezas del repo · {len(errores)} errores")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
