#!/usr/bin/env python3
"""usage-meter.py — coste real de generación de artefactos y tareas (iniciativa coste-generacion).

Mide los TOKENS REALES consumidos por una ventana de trabajo (generar una spec, una
evaluación, un plan, una tarea T-XX) leyendo las transcripciones JSONL de Claude Code,
y los convierte a € (rates.json) y horas-IA (ratio tokens→hora, CALIBRATION > default).

Modelo confirmado con el usuario (2026-08-11):
  fechas = contexto · tokens = medida · horas = tokens × ratio calibrado (NUNCA reloj de pared).

Formato de la transcripción (verificado empíricamente, T-01 · 2026-08-11; codificación de la
carpeta corregida en 2026-09-10, ver T-01 de usage-meter-transcripts):
  - Carpeta: ~/.claude/projects/<cwd con todo carácter no alfanumérico → '-'>/*.jsonl
    (una por sesión; sidechains aparte)
  - Registros type=="assistant" llevan message.usage con:
      input_tokens, output_tokens, cache_creation_input_tokens, cache_read_input_tokens
    (más campos extra que se ignoran de forma tolerante).
  - ⚠️ Una misma respuesta del modelo puede aparecer en VARIOS registros (hasta 6 observados)
    con message.id idéntico y usage idéntico → hay que DEDUPLICAR por message.id
    (sin dedupe se sobrecontaría ~2,5×).
  - Los subagentes escriben su propio transcript en <sesión>/subagents/**/*.jsonl (a veces
    varios niveles de profundidad, p. ej. subagents/workflows/<id>/agent-*.jsonl); NO
    aparecen intercalados en el .jsonl principal de la sesión. Se buscan de forma
    RECURSIVA bajo la carpeta del proyecto (T-03 de usage-meter-transcripts, 2026-09-10;
    antes el glob era plano y perdía el 43,6 % de los tokens facturables sin avisar,
    publicándolo como `fuente: medido`). `isSidechain` puede acompañar esos registros
    pero NO es el mecanismo de localización ni hace falta leerlo: basta con recorrer
    todos los .jsonl de la carpeta (incluidas subcarpetas) dentro de la ventana. El
    dedupe por message.id es GLOBAL entre fichero principal y subagentes (un id
    repetido entre ambos cuenta una sola vez; medido en esta máquina: 0 intersecciones,
    pero el código no lo asume).

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
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

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


# tolerancia del filtro por timestamp (T-04): relojes de fichero vs. reloj del `start`
# pueden desfasar unos segundos; 60s evita descartar por error el primer registro real.
TIMESTAMP_TOLERANCIA_SEG = 60


def _parse_iso(texto):
    """Parsea un timestamp ISO-8601 (con o sin 'Z') a datetime AWARE en UTC; None si no es
    parseable — el filtro de ventana NUNCA descarta un registro por un timestamp raro.

    Un ISO sin zona (ni `Z` ni offset) se ASUME UTC (revisión R1, B-1): los transcripts de
    Claude Code siempre llevan `Z`; un marcador de `usage-state.json` editado a mano puede no
    llevarlo. Antes se devolvía *naive*, y comparar/restar ese valor contra un datetime aware
    (p. ej. `fin = _now_iso()`) lanzaba `TypeError` sin capturar en `cmd_close` (moría el
    proceso) o se perdía toda la ventana en `_sum_usage_window` (capturado por el `except
    Exception` de `cmd_close`, pero silenciosamente)."""
    if not texto or not isinstance(texto, str):
        return None
    try:
        dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


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


def _encode_cwd(cwd):
    """Codifica un `cwd` como lo hace Claude Code al nombrar su carpeta de transcripciones.

    Claude Code convierte TODO carácter no alfanumérico en `-` (verificado contra las
    carpetas reales de `~/.claude/projects/` en esta máquina, T-01 de
    usage-meter-transcripts, 2026-09-10). Esto incluye espacios, `.`, `:`, `/`, `\\` y también
    `_` (ninguna de las carpetas reales de esta máquina lo tenía, pero la regla
    `[^A-Za-z0-9]` lo cubre igual: no es un caso especial).

    Supuesto NO verificado: los caracteres no-ASCII (`ñ`, `é`, CJK, …) también encajan en
    `[^A-Za-z0-9]` y se mapearían a `-` (p. ej. `C:\\Users\\Muñoz\\repo` →
    `C--Users-Mu-oz-repo`); ninguna de las 14 carpetas reales de esta máquina tiene un
    carácter así, así que no está confirmado que Claude Code haga lo mismo. Si Claude Code
    tratara el no-ASCII de otra forma, la clave no coincidiría y `close` degradaría en
    silencio a `fuente: estimado` — el mismo síntoma que motivó T-01, con otra clase de
    carácter.
    """
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def _project_transcript_dir():
    """Carpeta de transcripciones del proyecto actual (~/.claude/projects/<cwd codificado>)."""
    encoded = _encode_cwd(os.getcwd())
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


def _rel_key(f, tdir):
    """Clave estable de un transcript dentro de la carpeta del proyecto: ruta relativa
    en POSIX (no solo el nombre — los subagentes viven en subcarpetas y podrían, en
    teoría, repetir nombre de fichero entre sesiones distintas)."""
    return f.relative_to(tdir).as_posix()


def _snapshot_offsets(tdir):
    """Tamaño en bytes de cada .jsonl de la carpeta del proyecto, RECURSIVO (posición del
    marcador). Incluye <sesión>/subagents/**/*.jsonl (T-03 de usage-meter-transcripts,
    2026-09-10): antes solo miraba el nivel superior."""
    offsets = {}
    if tdir and Path(tdir).is_dir():
        tdir = Path(tdir)
        for f in tdir.rglob("*.jsonl"):
            try:
                offsets[_rel_key(f, tdir)] = f.stat().st_size
            except OSError:
                pass
    return offsets


# ------------------------------------------------------------------ medición

def _ventana_descarta(ts_dt, inicio_dt):
    """True si `ts_dt` cae antes de la ventana (`inicio_dt - TIMESTAMP_TOLERANCIA_SEG`);
    NUNCA descarta por una comparación imposible (defensivo: `_parse_iso` ya normaliza a
    aware UTC, así que esto no debería ocurrir en la práctica — B-1, revisión R1). Devuelve
    `(descarta, no_comparable)`. Extraída aparte para no anidar el `try` dentro del bucle
    de `_sum_usage_window` (regresión de anidamiento detectada por `code-health --baseline`,
    mismo patrón que la de T-04)."""
    try:
        return ts_dt < inicio_dt - timedelta(seconds=TIMESTAMP_TOLERANCIA_SEG), False
    except TypeError:
        return False, True


def _sum_usage_window(tdir, offsets, inicio=None):
    """Suma el usage de los registros NUEVOS (más allá del offset por fichero), con
    dedupe GLOBAL por message.id (registros repetidos de una misma respuesta, incluso
    entre el fichero principal y un subagente) y búsqueda RECURSIVA bajo la carpeta del
    proyecto: incluye <sesión>/subagents/**/*.jsonl (T-03 de usage-meter-transcripts,
    2026-09-10), también los creados tras el marcador (offset 0 para ficheros no vistos
    en el `start`, sean de la sesión principal o de un subagente lanzado en la ventana).

    `inicio` (str ISO-8601, opcional, T-04): si se da, descarta registros con
    `timestamp < inicio - TIMESTAMP_TOLERANCIA_SEG` — un marcador con offset 0 (fichero
    no visto en el `start`) ya NO cuenta enteros los transcripts previos a la ventana.
    Registros sin timestamp parseable NUNCA se descartan por este filtro (degradación
    honesta: se cuentan, como antes de T-04).

    Devuelve (tokens_dict, avisos:list). Lanza excepción solo ante fallo total de lectura.
    """
    seen = {}
    avisos = []
    tdir = Path(tdir)
    campos_malos = 0
    inicio_dt = _parse_iso(inicio) if inicio else None
    descartados_por_ventana = 0
    timestamps_no_comparables = 0
    for f in sorted(tdir.rglob("*.jsonl"), key=lambda p: _rel_key(p, tdir)):
        clave = _rel_key(f, tdir)
        start = offsets.get(clave, 0)
        if not isinstance(start, (int, float)) or start < 0:
            avisos.append(f"offset corrupto para {clave}; se relee completo")
            start = 0
        try:
            size = f.stat().st_size
            if size < start:
                # fichero truncado/rotado desde el marcador: releer completo con aviso
                avisos.append(f"{clave} truncado/rotado tras el marcador; se relee completo")
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
                    ts_dt = _parse_iso(rec.get("timestamp")) if inicio_dt is not None else None
                    descarta, no_comparable = _ventana_descarta(ts_dt, inicio_dt) \
                        if ts_dt is not None else (False, False)
                    if no_comparable:
                        timestamps_no_comparables += 1
                    if descarta:
                        descartados_por_ventana += 1
                        continue
                    msg = rec.get("message") or {}
                    usage = msg.get("usage") if isinstance(msg, dict) else None
                    if not isinstance(usage, dict):
                        continue
                    # dedupe por id de respuesta (una respuesta = hasta 6 registros idénticos);
                    # sin ningún id, clave única por posición para no colapsar respuestas distintas
                    mid = (msg.get("id") or rec.get("requestId") or rec.get("uuid")
                           or f"{clave}#{i}")
                    seen[mid] = usage  # la última repetición gana (son idénticas)
        except OSError as e:
            avisos.append(f"no se pudo leer {clave}: {e}")

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
    if descartados_por_ventana:
        avisos.append(f"{descartados_por_ventana} registro(s) anteriores al inicio de la ventana "
                       f"descartados (timestamp < inicio - {TIMESTAMP_TOLERANCIA_SEG}s)")
    if timestamps_no_comparables:
        avisos.append(f"{timestamps_no_comparables} registro(s) con timestamp no comparable "
                       f"contados igualmente (nunca se descarta por un timestamp raro)")
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
    marcador = {"version": 2, "inicio": _now_iso(), "transcriptDir": str(tdir) if tdir else None,
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
    elif marcador.get("version") != 2:
        # marcador abierto ANTES del arreglo T-04 (sin filtro por timestamp): medir su
        # ventana podría contar enteros transcripts previos al `start` → degradar, no mentir
        avisos.append("marcador anterior al arreglo (sin version); degradado a estimado")
    elif not marcador.get("inicio"):
        # marcador version=2 pero sin `inicio` (editado a mano o corrupto): sin `inicio` el
        # filtro por timestamp de `_sum_usage_window` queda desactivado en silencio y se vuelve
        # al bug exacto que T-04 arregla → degradar igual que "sin offsets"/"anterior al arreglo"
        # (B-5, revisión R1: `offsets` sí tenía esta defensa, `inicio` no)
        avisos.append("marcador sin `inicio` (¿corrupto o editado a mano?); degradado a estimado")
    else:
        tdir = args.transcript_dir or marcador.get("transcriptDir")
        if tdir and Path(tdir).is_dir():
            try:
                tokens, avs = _sum_usage_window(tdir, marcador.get("offsets") or {},
                                                 inicio=marcador.get("inicio"))
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

    # duracion_reloj (T-04, aditiva): fin - inicio real, formato fmt_horas; siempre que haya
    # marcador (independiente de si se pudo medir tokens) — NO sustituye a `duracion` (tokens
    # ÷ ratio, solo en fuente=medido); ambas conviven, `duracion` sigue siendo la que
    # consumen dashboards y plantillas existentes.
    dur_reloj = None
    inicio_dt = _parse_iso(resultado.get("inicio"))
    fin_dt = _parse_iso(fin)
    if inicio_dt is not None and fin_dt is not None:
        try:
            dur_reloj = fmt_horas(max((fin_dt - inicio_dt).total_seconds(), 0) / 3600)
        except (ValueError, OverflowError, TypeError):
            # TypeError defensivo (B-1, revisión R1): `_parse_iso` ya normaliza a aware UTC, pero
            # `close` NUNCA debe morir por una resta de fechas — degradación total, nunca bloquear
            dur_reloj = None

    if tokens and tokens["respuestas"] > 0:
        horas = _horas(tokens, ratio)
        try:
            dur = fmt_horas(horas) if horas is not None else None
        except (ValueError, OverflowError):
            dur = None
        resultado.update({"fuente": "medido", "tokens_reales": tokens,
                          "eur": _eur(tokens, rates, avisos),
                          "horas_ia": horas, "duracion": dur, "duracion_reloj": dur_reloj,
                          "ratio_usado": ratio, "ratio_origen": ratio_info})
    else:
        if tokens is not None and tokens["respuestas"] == 0:
            avisos.append("ventana sin respuestas del modelo (¿start y close seguidos?)")
        resultado.update({"fuente": "estimado", "tokens_reales": None, "eur": None,
                          "horas_ia": None, "duracion": None, "duracion_reloj": dur_reloj,
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
