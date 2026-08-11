#!/usr/bin/env python3
"""usage-meter.py — coste real de generación de artefactos y tareas (iniciativa coste-generacion).

Mide los TOKENS REALES consumidos por una ventana de trabajo (generar una spec, una
evaluación, un plan, una tarea T-XX) leyendo las transcripciones JSONL de Claude Code,
y los convierte a € (rates.json) y horas-IA (ratio tokens→hora, CALIBRATION > default).

Modelo confirmado con el usuario (2026-08-11):
  fechas = contexto · tokens = medida · horas = tokens × ratio calibrado (NUNCA reloj de pared).

Formato de la transcripción (verificado empíricamente, T-01 · 2026-08-11):
  - Carpeta: ~/.claude/projects/<cwd con '/'→'-'>/*.jsonl  (una por sesión; sidechains aparte)
  - Registros type=="assistant" llevan message.usage con:
      input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens
    (más campos extra que se ignoran de forma tolerante).
  - ⚠️ Una misma respuesta del modelo puede aparecer en VARIOS registros (hasta 6 observados)
    con message.id idéntico y usage idéntico → hay que DEDUPLICAR por message.id
    (sin dedupe se sobrecontaría ~2,5×).
  - isSidechain marca registros de subagentes; pueden vivir en el mismo fichero o en otros
    .jsonl de la carpeta → se suman TODOS los .jsonl de la carpeta dentro de la ventana.

El formato JSONL es interno de Claude Code (no API pública): ante cualquier problema de
lectura este script DEGRADA a fuente="estimado" y NUNCA bloquea (exit 0 salvo error de uso).

Uso:
  usage-meter.py start  --artefacto <clave> [--state FICHERO] [--transcript-dir DIR]
  usage-meter.py close  --artefacto <clave> [--state FICHERO] [--transcript-dir DIR]
                        [--rates FICHERO] [--calibration FICHERO] [--ratio N]
  usage-meter.py status [--state FICHERO]
  usage-meter.py fmt <horas>          # 0,53 → "32m" · 1,53 → "1h 32m" · 18 → "18h"

La clave --artefacto es una ruta o identificador estable (p. ej. docs/roadmap/<slug>/spec.md
o <slug>/T-03). `close` emite JSON por stdout; quien llama lo vuelca al bloque
`generacion:` del frontmatter (re-cerrar ACTUALIZA, no acumula).
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STATE = ".claude/usage-state.json"
# Ratio tokens→hora por defecto (NO calibrado; ver agent-kits/shared/estimation-defaults.md).
# Se calibra con /retro → docs/roadmap/CALIBRATION.md (mediana). Convención de facturables:
# input + creación de caché + output (la LECTURA de caché se informa pero no computa para
# horas: depende de la longitud de sesión, no del trabajo del artefacto).
DEFAULT_RATIO = 300_000
RATES_MAX_AGE_DAYS = 90


# ---------------------------------------------------------------- utilidades

def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt_horas(horas):
    """Horas decimales → estilo Jira compacto 'XhYm' (formato fijado por el usuario).

    0,53 → '32m' · 1,25 → '1h 15m' · 18,0 → '18h' · 0 → '0m'. Redondeo al minuto.
    Acepta coma o punto decimal si llega como texto.
    """
    if isinstance(horas, str):
        horas = float(horas.replace(",", "."))
    if horas < 0:
        raise ValueError("horas negativas")
    total_min = round(horas * 60)
    h, m = divmod(total_min, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def _project_transcript_dir():
    """Carpeta de transcripciones del proyecto actual (~/.claude/projects/<cwd '/'→'-'>)."""
    cwd = os.getcwd()
    encoded = re.sub(r"[/\\.:]", "-", cwd)
    for base in (Path.home() / ".claude" / "projects",
                 Path("/root/.claude/projects")):
        cand = base / encoded
        if cand.is_dir():
            return cand
    return None


def _load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_state(path, avisos=None):
    """Estado de marcadores, SIEMPRE un dict de dicts (state corrupto degrada, no rompe)."""
    raw = _load_json(path)
    if raw is None:
        if Path(path).is_file() and avisos is not None:
            avisos.append(f"state ilegible ({path}); se trata como vacío")
        return {}
    if not isinstance(raw, dict):
        if avisos is not None:
            avisos.append(f"state con forma inesperada ({type(raw).__name__}); se trata como vacío")
        return {}
    limpio = {}
    for k, v in raw.items():
        if isinstance(v, dict):
            limpio[k] = v
        elif avisos is not None:
            avisos.append(f"marcador corrupto descartado: {k}")
    return limpio


def _save_state(path, state, avisos=None):
    """Escritura atómica (temp + replace). Si falla, avisa y NO rompe el cierre."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)
    except OSError as e:
        if avisos is not None:
            avisos.append(f"no se pudo guardar el state: {e}")


def _snapshot_offsets(tdir):
    """Tamaño en bytes de cada .jsonl de la carpeta (posición del marcador)."""
    offsets = {}
    if tdir and Path(tdir).is_dir():
        for f in Path(tdir).glob("*.jsonl"):
            try:
                offsets[f.name] = f.stat().st_size
            except OSError:
                pass
    return offsets


# ------------------------------------------------------------------ medición

def _sum_usage_window(tdir, offsets):
    """Suma el usage de los registros NUEVOS (más allá del offset por fichero), con
    dedupe por message.id (registros repetidos de una misma respuesta) y sidechains
    incluidas (todos los .jsonl de la carpeta, también los creados tras el marcador).

    Devuelve (tokens_dict, avisos:list). Lanza excepción solo ante fallo total de lectura.
    """
    seen = {}
    avisos = []
    tdir = Path(tdir)
    campos_malos = 0
    for f in sorted(tdir.glob("*.jsonl")):
        start = offsets.get(f.name, 0)
        if not isinstance(start, (int, float)) or start < 0:
            avisos.append(f"offset corrupto para {f.name}; se relee completo")
            start = 0
        try:
            size = f.stat().st_size
            if size < start:
                # fichero truncado/rotado desde el marcador: releer completo con aviso
                avisos.append(f"{f.name} truncado/rotado tras el marcador; se relee completo")
                start = 0
            if size <= start:
                continue
            with open(f, encoding="utf-8", errors="replace") as fh:
                if start:
                    # el marcador normalmente cae en frontera de línea (snapshot = tamaño
                    # del fichero tras una escritura completa); solo hay que descartar
                    # fragmento si el byte anterior NO es un salto de línea
                    fh.seek(int(start) - 1)
                    if fh.read(1) != "\n":
                        fh.readline()
                for i, line in enumerate(fh):
                    try:
                        rec = json.loads(line)
                    except Exception:
                        continue  # línea corrupta/incompleta: tolerante
                    if not isinstance(rec, dict) or rec.get("type") != "assistant":
                        continue
                    msg = rec.get("message") or {}
                    usage = msg.get("usage") if isinstance(msg, dict) else None
                    if not isinstance(usage, dict):
                        continue
                    # dedupe por id de respuesta (una respuesta = hasta 6 registros idénticos);
                    # sin ningún id, clave única por posición para no colapsar respuestas distintas
                    mid = (msg.get("id") or rec.get("requestId") or rec.get("uuid")
                           or f"{f.name}#{i}")
                    seen[mid] = usage  # la última repetición gana (son idénticas)
        except OSError as e:
            avisos.append(f"no se pudo leer {f.name}: {e}")

    def _int(u, campo):
        nonlocal campos_malos
        v = u.get(campo) or 0
        try:
            return int(v)
        except (TypeError, ValueError):
            campos_malos += 1
            return 0
    tokens = {"entrada": 0, "salida": 0, "cache_creacion": 0, "cache_lectura": 0}
    for u in seen.values():
        tokens["entrada"] += _int(u, "input_tokens")
        tokens["salida"] += _int(u, "output_tokens")
        tokens["cache_creacion"] += _int(u, "cache_creation_input_tokens")
        tokens["cache_lectura"] += _int(u, "cache_read_input_tokens")
    if campos_malos:
        avisos.append(f"{campos_malos} campo(s) de usage no numéricos ignorados (contados como 0)")
    tokens["respuestas"] = len(seen)
    return tokens, avisos


# ----------------------------------------------------------- conversión €/h

def _find_rates(explicit):
    if explicit:
        return _load_json(explicit)
    for base in (Path.cwd() / ".claude", Path.home() / ".claude"):
        cand = base / "rates.json"
        if cand.is_file():
            return _load_json(cand)
    return None


def _precios_fiables(rates):
    """Regla vigente (estimation-defaults): input/output > 0 y verificadoEl < 90 días."""
    if not rates:
        return False
    pt = rates.get("precioTokens") or {}
    if not (pt.get("input") and pt.get("output")):
        return False
    verificado = pt.get("verificadoEl")
    if not verificado:
        return False
    try:
        edad = (datetime.now(timezone.utc)
                - datetime.fromisoformat(str(verificado)).replace(tzinfo=timezone.utc)).days
    except ValueError:
        return False
    return edad < RATES_MAX_AGE_DAYS


def _eur(tokens, rates, avisos):
    """€ de la ventana. Caché: solo se valora si rates.json trae precios de caché
    (precioTokens.cacheCreacion / cacheLectura); si no, se informa en tokens y se
    valora a 0 con aviso (regla de la spec: no inventar precios)."""
    if not _precios_fiables(rates):
        avisos.append("precioTokens no fiable (0/ausente/viejo) → eur=null; ejecuta la skill rates-verify")
        return None
    pt = rates["precioTokens"]
    if pt.get("moneda", "USD") == "USD":
        fx = rates.get("tipoCambioUsdEur")
        if not fx:
            avisos.append("precioTokens en USD sin tipoCambioUsdEur → eur=null (no se asume paridad)")
            return None
    else:
        fx = 1
    eur = (tokens["entrada"] * pt["input"] + tokens["salida"] * pt["output"]) / 1e6 * fx
    for campo, clave in (("cache_creacion", "cacheCreacion"), ("cache_lectura", "cacheLectura")):
        if pt.get(clave):
            eur += tokens[campo] * pt[clave] / 1e6 * fx
        elif tokens[campo]:
            avisos.append(f"{campo} sin precio en rates.json → valorada a 0 €")
    return round(eur, 2)


# rango de cordura del ratio tokens→hora: fuera de esto es casi seguro un error de
# formato/parseo, no un dato real (≈ entre 10k y 10M tokens facturables por hora-IA)
RATIO_MIN, RATIO_MAX = 10_000, 10_000_000


def _parse_ratio_cell(cell):
    """Número de una celda de CALIBRATION.md, tolerando notación humana:
    '300000' · '300.000' / '300,000' (miles) · '300k' · '0.3M' · '~250000'."""
    m = re.search(r"([\d]+(?:[.,]\d+)*)\s*([kKmM]?)", cell.replace("~", ""))
    if not m:
        return None
    num, suf = m.group(1), m.group(2).lower()
    # separadores de miles (europeo o US): grupos de 3 → quitar; si no, coma = decimal
    if re.fullmatch(r"\d{1,3}(?:[.,]\d{3})+", num):
        num = re.sub(r"[.,]", "", num)
    else:
        num = num.replace(",", ".")
    try:
        v = float(num)
    except ValueError:
        return None
    return v * 1000 if suf == "k" else v * 1_000_000 if suf == "m" else v


def _ratio_calibrado(calibration_path, avisos=None):
    """Mediana de la columna 'tokens/hora' de CALIBRATION.md (si existe). Devuelve
    (ratio, n_muestras) o (None, 0). Parser tolerante de tabla markdown: SOLO lee la
    tabla cuyo encabezado contiene 'tokens/hora' (se detiene al acabar esa tabla) y
    descarta con aviso los valores fuera del rango de cordura [10k, 10M]."""
    try:
        text = Path(calibration_path).read_text(encoding="utf-8")
    except OSError:
        return None, 0
    filas, col, en_tabla = [], None, False
    for line in text.splitlines():
        if "|" not in line:
            if en_tabla:
                break  # fin de LA tabla del encabezado; no leer tablas posteriores
            continue
        celdas = [c.strip() for c in line.strip().strip("|").split("|")]
        if col is None:
            for i, c in enumerate(celdas):
                if "tokens/hora" in c.lower():
                    col, en_tabla = i, True
                    break
            continue
        if set("".join(celdas)) <= set("-: "):
            continue  # separador |---|---|
        if col < len(celdas):
            v = _parse_ratio_cell(celdas[col])
            if v is None:
                continue
            if RATIO_MIN <= v <= RATIO_MAX:
                filas.append(v)
            elif avisos is not None:
                avisos.append(f"CALIBRATION: ratio {v:g} fuera de rango [10k,10M]; descartado")
    if not filas:
        return None, 0
    filas.sort()
    n = len(filas)
    mediana = filas[n // 2] if n % 2 else (filas[n // 2 - 1] + filas[n // 2]) / 2
    return mediana, n


def _horas(tokens, ratio):
    """horas_ia = facturables ÷ ratio. Facturables = entrada + creación de caché + salida
    (la lectura de caché queda fuera: mide longitud de sesión, no trabajo del artefacto)."""
    facturables = tokens["entrada"] + tokens["cache_creacion"] + tokens["salida"]
    return round(facturables / ratio, 2) if ratio else None


# ------------------------------------------------------------------ comandos

def cmd_start(args):
    avisos = []
    tdir = args.transcript_dir or _project_transcript_dir()
    state = _load_state(args.state, avisos)
    marcador = {"inicio": _now_iso(), "transcriptDir": str(tdir) if tdir else None,
                "offsets": _snapshot_offsets(tdir)}
    if not tdir:
        marcador["aviso"] = "transcripciones no localizadas; close degradará a fuente=estimado"
    state[args.artefacto] = marcador
    _save_state(args.state, state, avisos)
    salida = {"ok": True, "artefacto": args.artefacto,
              "inicio": marcador["inicio"], "ficheros": len(marcador["offsets"])}
    if avisos:
        salida["avisos"] = avisos
    print(json.dumps(salida, ensure_ascii=False))
    return 0


def cmd_close(args):
    avisos = []
    state = _load_state(args.state, avisos)
    marcador = state.get(args.artefacto)
    fin = _now_iso()
    resultado = {"artefacto": args.artefacto,
                 "inicio": marcador.get("inicio") if marcador else None, "fin": fin}
    tokens = None
    if not marcador:
        avisos.append("sin marcador start para este artefacto")
    elif "offsets" not in marcador:
        # marcador sin offsets (escrito a mano o de otra versión): medir sería contar
        # TODO el histórico como ventana → degradar con aviso, no mentir
        avisos.append("marcador sin offsets (¿corrupto o de otra versión?); degradado a estimado")
    else:
        tdir = args.transcript_dir or marcador.get("transcriptDir")
        if tdir and Path(tdir).is_dir():
            try:
                tokens, avs = _sum_usage_window(tdir, marcador.get("offsets") or {})
                avisos += avs
            except Exception as e:  # degradación total: nunca bloquear
                avisos.append(f"lectura de transcripciones falló: {e}")
        else:
            avisos.append("carpeta de transcripciones no disponible")

    rates = _find_rates(args.rates)
    if args.ratio is not None:
        ratio, ratio_info = args.ratio, f"explícito ({args.ratio:g})"
    else:
        ratio, n = _ratio_calibrado(args.calibration or "docs/roadmap/CALIBRATION.md", avisos)
        ratio_info = (f"CALIBRATION.md (mediana de {n})" if ratio
                      else f"default no calibrado ({DEFAULT_RATIO})")
        ratio = ratio or DEFAULT_RATIO

    if tokens and tokens["respuestas"] > 0:
        horas = _horas(tokens, ratio)
        try:
            dur = fmt_horas(horas) if horas is not None else None
        except (ValueError, OverflowError):
            dur = None
        resultado.update({"fuente": "medido", "tokens_reales": tokens,
                          "eur": _eur(tokens, rates, avisos),
                          "horas_ia": horas, "duracion": dur,
                          "ratio_usado": ratio, "ratio_origen": ratio_info})
    else:
        if tokens is not None and tokens["respuestas"] == 0:
            avisos.append("ventana sin respuestas del modelo (¿start y close seguidos?)")
        resultado.update({"fuente": "estimado", "tokens_reales": None, "eur": None,
                          "horas_ia": None, "duracion": None,
                          "ratio_usado": ratio, "ratio_origen": ratio_info,
                          "nota": "estima tokens/horas a juicio y márcalo como estimado"})
    if marcador:
        marcador["ultimoCierre"] = fin  # el marcador se conserva: re-close = misma ventana actualizada
        _save_state(args.state, state, avisos)
    if avisos:
        resultado["avisos"] = avisos
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 0


def cmd_status(args):
    state = _load_state(args.state)
    ahora = datetime.now(timezone.utc)
    out = []
    for clave, m in state.items():
        edad_h = None
        try:
            edad_h = round((ahora - datetime.fromisoformat(
                m["inicio"].replace("Z", "+00:00"))).total_seconds() / 3600, 1)
        except (KeyError, ValueError):
            pass
        out.append({"artefacto": clave, "inicio": m.get("inicio"),
                    "cerrado": "ultimoCierre" in m, "horas_desde_inicio": edad_h})
    print(json.dumps({"marcadores": out}, ensure_ascii=False, indent=2))
    return 0


def cmd_fmt(args):
    try:
        print(fmt_horas(args.horas))
        return 0
    except (ValueError, OverflowError) as e:
        print(json.dumps({"error": str(e) or "valor no representable"}))
        return 2


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    def comunes(sp):
        sp.add_argument("--artefacto", required=True,
                        help="clave estable del artefacto/tarea (ruta o <slug>/T-XX)")
        sp.add_argument("--state", default=DEFAULT_STATE)
        sp.add_argument("--transcript-dir", default=None,
                        help="carpeta de transcripciones (tests/entornos raros)")

    sp = sub.add_parser("start", help="marca el inicio de la ventana")
    comunes(sp)
    sp.set_defaults(fn=cmd_start)

    sp = sub.add_parser("close", help="cierra la ventana y emite el JSON de generacion:")
    comunes(sp)
    sp.add_argument("--rates", default=None, help="ruta a rates.json (default: autodetección)")
    sp.add_argument("--calibration", default=None, help="ruta a CALIBRATION.md")
    def _ratio_pos(v):
        f = float(v)
        if not f > 0:
            raise argparse.ArgumentTypeError("el ratio debe ser > 0")
        return f
    sp.add_argument("--ratio", type=_ratio_pos, default=None,
                    help="ratio tokens→hora explícito (> 0)")
    sp.set_defaults(fn=cmd_close)

    sp = sub.add_parser("status", help="lista marcadores (huérfanos incluidos)")
    sp.add_argument("--state", default=DEFAULT_STATE)
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("fmt", help="horas decimales → formato humano XhYm")
    sp.add_argument("horas")
    sp.set_defaults(fn=cmd_fmt)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
