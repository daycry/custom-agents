#!/usr/bin/env python3
"""
ledger-archive.py — archivado DETERMINISTA de la historia cerrada del ledger canónico `tasks.md`.

`tasks.md` crece sin límite y acaba superando el tope de lectura acotada de 256 KiB
(`local-read.py` `MAX_BYTES`, que usan la retoma `progress-report.py resume` y `plan-review.py`).
Lo que más pesa es historia ya cerrada: secciones `## Revisión de dos lentes — intento N`
superadas y campos `- **Verificación**:` con narrativa acumulada. Este script la traslada a
`<carpeta>/execution-history.md` con los bytes intactos y su SHA-256, y deja en el ledger un
puntero por bloque. Sustituye al traslado a mano (`## Traslado AAAA-MM-DD …`).

A) Secciones de revisión archivables. Candidata si (a) ninguna de sus filas está pendiente
   (`gap_pendiente`), (b) no es la última sección de revisión del fichero y (c) una sección
   POSTERIOR la supera (sus menciones efectivas incluyen todas las de esta). Selección POR
   INVARIANTE: de la más antigua a la más reciente, una candidata se archiva solo si, al quitarla,
   para TODAS las tareas `T-NN` (las del ledger y las citadas en revisiones) siguen idénticos
   `filas_pendientes_de_tarea` (intento y filas: gap/tarea/grado) y `ultimo_intento_para`, el
   intento máximo global no cambia, la lista de tareas tampoco y NINGUNA sección que queda cambia
   sus menciones efectivas (una ronda anónima «sin gaps» no pasa a heredar de otra). Así
   `jira-flow aprobado`, el brief de `task-brief.py` y `ledger-lint` dan lo mismo antes y después.
   Las pasadas se repiten hasta el punto fijo: una segunda ejecución no archiva nada. Cada sección
   archivada deja una línea en `## Historial archivado` (al final del ledger; sin cabecera doble).
B) `Verificación` de más de `--verificacion-max` caracteres (por defecto el `VERIFICACION_MAX` de
   `ledger-lint.py`): se sustituye por su PRIMERA frase (hasta el primer «. » o 400 caracteres, sin
   cortar palabras) + ` Detalle archivado: [execution-history.md](execution-history.md) · SHA-256
   `<sha12>`.`; el campo sigue presente (`verificacion: obligatoria`).
C) Histórico: una sección `## Archivado AAAA-MM-DD — <qué> (bytes sin cambios)` por bloque, con
   `SHA-256 del bloque: `<sha>`.` y el bloque tal cual. IDEMPOTENTE: un SHA que ya está en el
   histórico no se vuelve a añadir (cubre un corte entre las dos escrituras). El SHA se calcula
   sobre el bloque con finales LF (UTF-8), lo que ve git tras normalizar (GOT-007). El ledger
   conserva su final de línea (CRLF/LF; uno mixto queda con el dominante). El histórico es de SOLO
   AÑADIR: lo previo no se re-codifica nunca, lo añadido lleva su final dominante y uno nuevo nace
   con el del ledger.
   Escrituras atómicas (temporal hermano + `os.replace`): primero el histórico, después el ledger.
   Antes de escribir verifica que `ledger-lint` no da MÁS incoherencias que antes y que los
   invariantes de (A) se mantienen; si no, no escribe nada y sale con 1.

El parser es el de `ledger-lint.py` (cargado con importlib, sin duplicarlo).

Uso:
  ledger-archive.py <carpeta-iniciativa> [--apply] [--verificacion-max N] [--json] [--fecha AAAA-MM-DD]
  Sin --apply: plan en seco (no escribe nada). Lo ejecuta el ORQUESTADOR cuando `ledger-lint` avisa
  del tamaño (el implementer no: su guardia solo le deja escribir `tasks.md` en `docs/roadmap/`).
Exit: 0 éxito (también «nada que archivar») · 1 la verificación posterior falla (nada escrito) ·
      2 error de uso (carpeta sin `tasks.md`, ledger o histórico ilegibles, fecha inválida).
"""
import argparse
import bisect
import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
HISTORICO = "execution-history.md"
HISTORIAL_HDR = "## Historial archivado"
PUNTERO = f"[{HISTORICO}]({HISTORICO})"
FRASE_MAX = 400
_FECHA_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TAREA_HDR_RE = re.compile(r"^###\s+(T-\d+)\b")
_H2_RE = re.compile(r"^##\s")
_FASE_H3_RE = re.compile(r"^###\s+Fase\b")


def _cargar_ledger_lint():
    """`ledger-lint.py` por ruta (mismo patrón que `scope-check.py` y `jira-flow.py`)."""
    spec = importlib.util.spec_from_file_location("ledger_lint_archive",
                                                  os.path.join(HERE, "ledger-lint.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


LL = _cargar_ledger_lint()


def sha256(texto):
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ------------------------------------------------------------------ secciones de revisión ----

def bloques_revision(texto):
    """`secciones_revision()` con `a`/`b`: el rango del bloque en `texto`. `secciones_revision`
    calcula `inicio`/`fin` sobre `sin_vallas(texto)`, que conserva el número de líneas pero no su
    longitud: se traducen por número de línea (cabeceras y `fin` caen siempre a inicio de línea)."""
    secs = LL.secciones_revision(texto)
    if not secs:
        return secs
    limpio = LL.sin_vallas(texto)
    nl_limpio = [i for i, c in enumerate(limpio) if c == "\n"]
    inicios = [0] + [i + 1 for i, c in enumerate(texto) if c == "\n"]

    def orig(p):
        if p >= len(limpio):
            return len(texto)
        return inicios[bisect.bisect_left(nl_limpio, p)]

    for s in secs:
        s["a"], s["b"] = orig(s["inicio"]), orig(s["fin"])
    return secs


def sin_almohadillas(cabecera):
    return re.sub(r"^#+\s*", "", cabecera).strip()


def invariantes(texto):
    """Lo que `jira-flow aprobado`, `task-brief.py` y `ledger-lint` deciden sobre cada tarea."""
    secs = LL.secciones_revision(texto)
    ids = [t["id"] for t in LL.parse_ledger(texto)["tareas"]]
    tareas = set(ids)
    for s in secs:
        tareas |= LL.menciones(s)
    out = {"__tareas__": ids, "__max__": max((s["intento"] for s in secs), default=None)}
    for t in sorted(tareas):
        intento, filas = LL.filas_pendientes_de_tarea(secs, t)
        out[t] = {"pendientes": (intento, [(f["gap"], f["tarea"], f["grado"]) for f in filas]),
                  "ultimo_intento": LL.ultimo_intento_para(secs, [t])}
    return out


def diferencia(base, nuevo):
    """Primera diferencia legible entre dos `invariantes()`, o None si son iguales."""
    if base["__tareas__"] != nuevo["__tareas__"]:
        return "cambiaría la lista de tareas del ledger"
    if base["__max__"] != nuevo["__max__"]:
        return f"intento máximo global {base['__max__']} → {nuevo['__max__']}"
    for t in sorted(set(base) | set(nuevo)):
        if t.startswith("__"):
            continue
        a, b = base.get(t), nuevo.get(t)
        if a is None or b is None:
            return f"{t} dejaría de ser citada" if b is None else f"{t} aparecería"
        if a["ultimo_intento"] != b["ultimo_intento"]:
            return f"{t}: último intento {a['ultimo_intento']} → {b['ultimo_intento']}"
        if a["pendientes"] != b["pendientes"]:
            return (f"{t}: evidencia de pendientes cambiaría (intento {a['pendientes'][0]} → "
                    f"{b['pendientes'][0]}, {len(a['pendientes'][1])} → {len(b['pendientes'][1])} fila(s))")
    return None


def motivo_no_candidata(secs, i, efectivas):
    s = secs[i]
    pendientes = [f for f in s["filas"] if LL.gap_pendiente(f)]
    if pendientes:
        return f"tiene {len(pendientes)} fila(s) pendiente(s)"
    if i == len(secs) - 1:
        return "es la última sección de revisión del fichero"
    if not any(efectivas[j] >= efectivas[i] for j in range(i + 1, len(secs))):
        cita = ", ".join(sorted(efectivas[i])) or "ninguna tarea"
        return f"ninguna sección posterior la supera (menciona {cita})"
    return None


def herencia_cambiada(secs, i, efectivas, nuevo):
    """Cabecera de la primera sección que, al quitar `secs[i]`, cambiaría sus menciones EFECTIVAS
    (una ronda anónima «sin gaps» que pasaría a heredar de otra sección), o None. Sin esta
    comprobación, un cambio de herencia sin efecto en ninguna tarea abría candidatas nuevas en la
    siguiente ejecución (no idempotente: lo destapó el ledger real de catalog-capabilities)."""
    despues = LL._menciones_efectivas(LL.secciones_revision(nuevo))
    resto = efectivas[:i] + efectivas[i + 1:]
    for k, (a, b) in enumerate(zip(resto, despues)):
        if a != b:
            return sin_almohadillas(secs[k + (k >= i)]["cabecera"])
    return None


def _una_pasada(texto, base):
    cur, archivadas, omitidas, i = texto, [], [], 0
    while True:
        secs = bloques_revision(cur)
        if i >= len(secs):
            break
        s = secs[i]
        efectivas = LL._menciones_efectivas(secs)
        motivo = motivo_no_candidata(secs, i, efectivas)
        if motivo is None:
            nuevo = cur[:s["a"]] + cur[s["b"]:]
            dif = diferencia(base, invariantes(nuevo))
            otra = None if dif else herencia_cambiada(secs, i, efectivas, nuevo)
            if dif is None and otra is None:
                archivadas.append({"cabecera": sin_almohadillas(s["cabecera"]),
                                   "bloque": cur[s["a"]:s["b"]]})
                cur = nuevo
                continue                    # la siguiente sección ocupa ahora la posición i
            motivo = (f"invariante: {dif}" if dif else
                      f"invariante: cambiaría la herencia de «{otra[:70]}»")
        omitidas.append({"cabecera": sin_almohadillas(s["cabecera"]), "motivo": motivo})
        i += 1
    return cur, archivadas, omitidas


def seleccionar_revisiones(texto, base):
    """(texto sin las secciones archivadas, [archivadas], [omitidas]): pasadas greedy por invariante
    hasta el PUNTO FIJO (una pasada que no archiva nada), para que una segunda ejecución no encuentre
    candidatas nuevas. `omitidas` son las de la última pasada: las que se quedan."""
    cur, archivadas = texto, []
    while True:
        cur, nuevas, omitidas = _una_pasada(cur, base)
        archivadas += nuevas
        if not nuevas:
            return cur, archivadas, omitidas


# ------------------------------------------------------------------------ Verificación ----

def primera_frase(s, tope=FRASE_MAX):
    """Hasta el primer «. » o `tope` caracteres, lo que llegue antes, sin cortar a mitad de palabra."""
    k = s.find(". ")
    if 0 <= k < tope:
        return s[:k + 1]
    if len(s) <= tope:
        return s
    corte = s[:tope]
    if not s[tope].isspace():
        partes = corte.rsplit(None, 1)
        if len(partes) == 2:
            corte = partes[0]
    return corte.rstrip() + "…"


def recortar_verificaciones(texto, maximo):
    """(texto con las `Verificación` largas recortadas, [{tarea, bloque, sha}]). Mismo criterio de
    campo que `parse_ledger`: la PRIMERA `Verificación` de cada `### T-NN` (un `## ` o `### Fase`
    cierra la tarea), con su sub-lista (`parse_verificacion`) y sus continuaciones de prosa."""
    lineas = texto.split("\n")
    limpias = LL.sin_vallas(texto).split("\n")
    cambios, tarea, vistas, i = [], None, set(), 0
    while i < len(limpias):
        ln = limpias[i]
        m = _TAREA_HDR_RE.match(ln)
        if m:
            tarea = m.group(1)
        elif _H2_RE.match(ln) or _FASE_H3_RE.match(ln):
            tarea = None
        elif tarea and tarea not in vistas and LL.VERIF_RE.match(ln):
            vistas.add(tarea)
            info, j = LL.parse_verificacion(limpias, i)
            cont = []
            while j < len(limpias) and LL.es_continuacion(limpias[j]):
                cont.append(limpias[j].strip())
                j += 1
            campo = " ".join([" · ".join(info["items"])] + cont).strip()
            if len(campo) > maximo:
                cambios.append((tarea, i, j, campo))
            i = j
            continue
        i += 1
    out = []
    for tarea, i, j, campo in reversed(cambios):         # de abajo arriba: los índices no se mueven
        bloque = "\n".join(lineas[i:j]) + "\n"
        sha = sha256(bloque)
        m = LL.VERIF_RE.match(lineas[i])
        prefijo = lineas[i][:m.start("inline")].rstrip() + " "
        lineas[i:j] = [f"{prefijo}{primera_frase(campo)} Detalle archivado: {PUNTERO} · "
                       f"SHA-256 `{sha[:12]}`."]
        out.append({"tarea": tarea, "bloque": bloque, "sha": sha})
    return "\n".join(lineas), list(reversed(out))


# ------------------------------------------------------------------- Historial archivado ----

def anadir_historial(texto, nuevas):
    """Añade `nuevas` líneas a `## Historial archivado` (al final del ledger si no existe)."""
    if not nuevas:
        return texto
    lineas = texto.split("\n")
    limpias = LL.sin_vallas(texto).split("\n")
    idx = next((k for k, ln in enumerate(limpias) if ln.strip() == HISTORIAL_HDR), None)
    if idx is None:
        return texto.rstrip("\n") + "\n\n" + HISTORIAL_HDR + "\n\n" + "\n".join(nuevas) + "\n"
    fin = next((k for k in range(idx + 1, len(limpias)) if _H2_RE.match(limpias[k])), len(lineas))
    ultimo = max((k for k in range(idx + 1, fin) if lineas[k].strip()), default=None)
    if ultimo is None:
        lineas[idx + 1:idx + 1] = [""] + nuevas
    else:
        lineas[ultimo + 1:ultimo + 1] = nuevas
    return "\n".join(lineas)


def componer_historico(previo, slug, entradas, fecha):
    """Texto (LF) del histórico con las entradas cuyo SHA aún no contiene; (texto, añadidas)."""
    h = previo if previo is not None else f"# Historial de ejecución — {slug}\n"
    anadidas = 0
    for e in entradas:
        if e["sha"] in h:
            continue
        if not h.endswith("\n"):
            h += "\n"
        bloque = e["bloque"] if e["bloque"].endswith("\n") else e["bloque"] + "\n"
        h += (f"\n## Archivado {fecha} — {e['titulo']} (bytes sin cambios)\n\n"
              f"SHA-256 del bloque: `{e['sha']}`.\n\n{bloque}")
        anadidas += 1
    return h, anadidas


# ------------------------------------------------------------------------------- E/S ----

def newline_dominante(texto, defecto="\n"):
    """`\r\n` o `\n`, el que más aparece (un fichero mixto conserva su mayoría); `defecto` sin saltos."""
    crlf = texto.count("\r\n")
    lf = texto.count("\n") - crlf
    if not crlf and not lf:
        return defecto
    return "\r\n" if crlf > lf else "\n"


BOM = chr(0xFEFF)           # BOM UTF-8


def leer_texto(path):
    """(texto LF sin BOM, bom, newline dominante) o lanza UnicodeDecodeError/OSError."""
    with open(path, "rb") as fh:
        texto = fh.read().decode("utf-8")
    bom = texto.startswith(BOM)
    if bom:
        texto = texto[1:]
    return texto.replace("\r\n", "\n"), bom, newline_dominante(texto)


def a_bytes(texto, bom, nl):
    return ((BOM if bom else "") + texto.replace("\n", nl)).encode("utf-8")


def escribir_atomico(path, data):
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", suffix=".tmp",
                               dir=os.path.dirname(path) or ".")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def errores_lint(data):
    """Incoherencias de `ledger-lint` sobre `data` (bytes), en un temporal FUERA del repo."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "tasks.md")
        with open(p, "wb") as fh:
            fh.write(data)
        return LL.lint(p)[0]


def slug_de(carpeta):
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", os.path.basename(os.path.normpath(carpeta)))


def planificar(carpeta, maximo, fecha):
    """Calcula todo sin escribir. Devuelve un dict con el plan y los bytes resultantes."""
    tasks = os.path.join(carpeta, "tasks.md")
    texto, bom, nl = leer_texto(tasks)
    base = invariantes(texto)
    tras_a, archivadas, omitidas = seleccionar_revisiones(texto, base)
    tras_b, recortes = recortar_verificaciones(tras_a, maximo)
    for a in archivadas:
        a["sha"] = sha256(a["bloque"])
    final = anadir_historial(tras_b, [
        f"- {fecha} · «{a['cabecera']}» → {PUNTERO} · SHA-256 `{a['sha']}`" for a in archivadas])
    antes = a_bytes(texto, bom, nl)
    despues = a_bytes(final, bom, nl) if (archivadas or recortes) else antes
    entradas = ([{"titulo": a["cabecera"], "bloque": a["bloque"], "sha": a["sha"]} for a in archivadas]
                + [{"titulo": f"{r['tarea']} · Verificación", "bloque": r["bloque"], "sha": r["sha"]}
                   for r in recortes])
    return {"tasks": tasks, "texto": texto, "final": final, "nl": nl, "base": base,
            "antes": antes, "despues": despues, "archivadas": archivadas, "recortes": recortes,
            "omitidas": omitidas, "entradas": entradas}


def verificar(plan):
    """Motivo por el que el resultado NO es aceptable, o None."""
    if plan["despues"] == plan["antes"]:
        return None
    dif = diferencia(plan["base"], invariantes(plan["final"]))
    if dif:
        return f"los invariantes de revisión cambiarían: {dif}"
    e_antes, e_despues = errores_lint(plan["antes"]), errores_lint(plan["despues"])
    if len(e_despues) > len(e_antes):
        nuevas = [e for e in e_despues if e not in e_antes][:3]
        return (f"ledger-lint empeoraría: {len(e_antes)} → {len(e_despues)} incoherencias "
                f"({'; '.join(nuevas)})")
    return None


def aplicar(plan, carpeta, fecha):
    """Escribe el histórico y DESPUÉS el ledger; devuelve cuántos bloques se añadieron al histórico.
    El histórico es de SOLO AÑADIR: sus bytes previos no se re-codifican nunca (el real mezcla CRLF
    y LF); lo añadido usa su final de línea dominante (uno nuevo, el del ledger)."""
    hist_path = os.path.join(carpeta, HISTORICO)
    if os.path.exists(hist_path):
        with open(hist_path, "rb") as fh:
            raw = fh.read()
        previo = raw.decode("utf-8")                      # ilegible → UnicodeDecodeError, nada escrito
        nl = newline_dominante(previo, plan["nl"])
        previo_lf = previo.replace("\r\n", "\n")
        nuevo, anadidas = componer_historico(previo_lf, slug_de(carpeta), plan["entradas"], fecha)
        datos = raw + nuevo[len(previo_lf):].replace("\n", nl).encode("utf-8")
    else:
        nuevo, anadidas = componer_historico(None, slug_de(carpeta), plan["entradas"], fecha)
        datos = a_bytes(nuevo, False, plan["nl"])
    if anadidas:
        escribir_atomico(hist_path, datos)
    escribir_atomico(plan["tasks"], plan["despues"])
    return anadidas


def bloque_en_fichero(bloque, nl):
    return len(bloque.replace("\n", nl).encode("utf-8"))


def informe(plan, aplicado):
    nl = plan["nl"]
    return {
        "aplicado": aplicado,
        "secciones": [{"cabecera": a["cabecera"], "sha256": a["sha"],
                       "bytes": bloque_en_fichero(a["bloque"], nl)} for a in plan["archivadas"]],
        "verificaciones": [{"tarea": r["tarea"], "sha256": r["sha"],
                            "bytes": bloque_en_fichero(r["bloque"], nl)} for r in plan["recortes"]],
        "bytes_antes": len(plan["antes"]),
        "bytes_despues": len(plan["despues"]),
        "omitidas": plan["omitidas"],
    }


def imprimir(d, carpeta):
    modo = "aplicado" if d["aplicado"] else "en seco — nada escrito; --apply para aplicar"
    print(f"ledger-archive ({modo}): {carpeta}")
    if not d["secciones"] and not d["verificaciones"]:
        print("  nada que archivar")
    if d["secciones"]:
        print(f"  secciones de revisión archivadas ({len(d['secciones'])}):")
        for s in d["secciones"]:
            print(f"    - «{s['cabecera']}» · {s['bytes']} bytes · SHA-256 {s['sha256'][:12]}")
    if d["verificaciones"]:
        print(f"  Verificación recortadas ({len(d['verificaciones'])}):")
        for v in d["verificaciones"]:
            print(f"    - {v['tarea']} · {v['bytes']} bytes · SHA-256 {v['sha256'][:12]}")
    if d["omitidas"]:
        print(f"  secciones de revisión que se quedan ({len(d['omitidas'])}):")
        for o in d["omitidas"]:
            print(f"    - «{o['cabecera'][:90]}»: {o['motivo']}")
    a, b = d["bytes_antes"], d["bytes_despues"]
    pct = f" ({(a - b) * 100 / a:.0f} % menos)" if a and b < a else ""
    print(f"  bytes: {a} → {b}{pct}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Archiva la historia cerrada del ledger tasks.md")
    ap.add_argument("carpeta", help="carpeta de la iniciativa (docs/roadmap/<fecha>-<slug>)")
    ap.add_argument("--apply", action="store_true", help="escribe (sin esto: plan en seco)")
    ap.add_argument("--verificacion-max", type=int, default=LL.VERIFICACION_MAX,
                    help=f"caracteres de Verificación a partir de los que se recorta "
                         f"(por defecto {LL.VERIFICACION_MAX})")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--fecha", default=None, help="fecha de las entradas (AAAA-MM-DD; hoy por defecto)")
    args = ap.parse_args(argv)

    fecha = args.fecha or datetime.date.today().isoformat()
    if not _FECHA_RE.match(fecha):
        print(f"ledger-archive: --fecha «{fecha}» no es AAAA-MM-DD", file=sys.stderr)
        return 2
    if args.verificacion_max < 1:
        print("ledger-archive: --verificacion-max tiene que ser un entero positivo", file=sys.stderr)
        return 2
    carpeta = args.carpeta
    if not os.path.isfile(os.path.join(carpeta, "tasks.md")):
        print(f"ledger-archive: no existe {os.path.join(carpeta, 'tasks.md')}", file=sys.stderr)
        return 2
    try:
        plan = planificar(carpeta, args.verificacion_max, fecha)
    except (OSError, UnicodeDecodeError) as e:
        print(f"ledger-archive: ledger ilegible ({e})", file=sys.stderr)
        return 2

    motivo = verificar(plan)
    if motivo:
        print(f"ledger-archive: no se escribe nada — {motivo}", file=sys.stderr)
        return 1
    aplicado = False
    if args.apply and plan["despues"] != plan["antes"]:
        try:
            aplicar(plan, carpeta, fecha)
        except UnicodeDecodeError as e:
            print(f"ledger-archive: histórico ilegible ({e}); no se escribe nada", file=sys.stderr)
            return 2
        aplicado = True                            # «aplicado» = se escribió algo
    d = informe(plan, aplicado)
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        imprimir(d, carpeta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
