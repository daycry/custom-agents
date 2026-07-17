#!/usr/bin/env python3
"""worklog.py — cálculo DETERMINISTA del worklog de jira-sync.

Saca de la prosa la parte delicada: qué horas imputar por tarea (IA + supervisión,
real→est), el TOPE DIARIO de jornada y el BANCO de horas por issue. El agente (LLM)
orquesta y llama a Jira; este script calcula y lleva el estado. Salida siempre JSON.

Comandos:
  plan   --task T-08 --issue KEY [--ia-real H --ia-est H --sup-real H --sup-est H
         --human-real H --human-est H] [--policy banco|parar|seguir|preguntar]
         [--fecha YYYY-MM-DD] [--apply]
         → cuánto imputar HOY a ese issue, cuánto va al banco y si hace falta decisión.
  drain  [--fecha YYYY-MM-DD] [--apply]
         → qué entradas del banco caben hoy (por issue), respetando la jornada.
  status → resumen del estado (imputado por día, banco pendiente).

Estado:  .claude/jira-state.json  (imputadoPorDia, bancoHoras[], tasks{})
Config:  .claude/rates.json (horasJornada, ratioSupervision) y .claude/jira.json
         (alCubrirJornada; horasJornada opcional que sobreescribe).
Sin dependencias externas (stdlib). Nunca imputa con fecha futura: 'plan' y 'drain'
operan sobre la fecha dada (hoy por defecto).
"""
import argparse
import datetime
import json
import os
import sys

DEF_JORNADA = 8.0
DEF_RATIO = 0.25


def find_up(names, start="."):
    """Busca .claude/<name> hacia arriba desde start; devuelve la primera ruta."""
    d = os.path.abspath(start)
    while True:
        for n in names:
            p = os.path.join(d, ".claude", n)
            if os.path.exists(p):
                return p
        nd = os.path.dirname(d)
        if nd == d:
            return None
        d = nd


def load_json(path, default):
    if not path or not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cfg(args):
    rates = load_json(args.rates or find_up(["rates.json"]), {})
    jira = load_json(args.jira or find_up(["jira.json"]), {})
    jornada = float(jira.get("horasJornada") or rates.get("horasJornada") or DEF_JORNADA)
    ratio = float(rates.get("ratioSupervision") or DEF_RATIO)
    policy = args.policy or jira.get("alCubrirJornada") or "preguntar"
    return jornada, ratio, policy


def state_path(args):
    return args.state or find_up(["jira-state.json"]) or os.path.join(".claude", "jira-state.json")


def load_state(args):
    st = load_json(state_path(args), {})
    st.setdefault("imputadoPorDia", {})
    st.setdefault("bancoHoras", [])
    st.setdefault("tasks", {})
    return st


def pick(real, est):
    return real if real is not None else est


def cmd_plan(args):
    jornada, ratio, policy = cfg(args)
    st = load_state(args)
    fecha = args.fecha or datetime.date.today().isoformat()

    ia = pick(args.ia_real, args.ia_est)
    sup = pick(args.sup_real, args.sup_est)
    if sup is None and ia is not None:
        sup = round(ia * ratio, 2)
    if ia is not None:
        horas = round(ia + (sup or 0), 2)
        base = "ia+supervision"
    else:  # fallback: tarea puramente humana
        horas = pick(args.human_real, args.human_est)
        base = "humano"
    if horas is None:
        print(json.dumps({"error": "sin horas: pasa --ia-real/--ia-est o --human-real/--human-est"}))
        return 2

    imputado = float(st["imputadoPorDia"].get(fecha, 0))
    restante = max(0.0, round(jornada - imputado, 2))
    out = {"task": args.task, "issue": args.issue, "fecha": fecha, "base": base,
           "horas": horas, "jornada": jornada, "imputadoHoy": imputado,
           "restanteJornada": restante, "politica": policy,
           "imputarHoy": 0.0, "banco": 0.0, "parar": False, "requiereDecision": False}

    if horas <= restante:
        out["imputarHoy"] = horas
    elif policy == "seguir":
        out["imputarHoy"] = horas
    elif policy in ("banco", "parar"):
        out["imputarHoy"] = restante
        out["banco"] = round(horas - restante, 2)
        out["parar"] = (policy == "parar")
    else:  # preguntar
        out["requiereDecision"] = True
        out["opciones"] = {
            "parar": f"imputar {restante}h hoy, bancar {round(horas-restante,2)}h y DETENER la implementación",
            "seguir": f"imputar las {horas}h completas aunque el día supere la jornada",
            "banco": f"imputar {restante}h hoy, bancar {round(horas-restante,2)}h y seguir implementando",
        }

    if args.apply and not out["requiereDecision"]:
        st["imputadoPorDia"][fecha] = round(imputado + out["imputarHoy"], 2)
        if out["banco"] > 0:
            st["bancoHoras"].append({"task": args.task, "issueKey": args.issue,
                                     "horas": out["banco"], "origen": fecha})
        t = st["tasks"].setdefault(args.task, {})
        t["issueKey"] = args.issue
        t["worklog"] = round(float(t.get("worklog", 0)) + out["imputarHoy"], 2)
        save_json(state_path(args), st)
        out["aplicado"] = True
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_drain(args):
    jornada, _, _ = cfg(args)
    st = load_state(args)
    fecha = args.fecha or datetime.date.today().isoformat()
    imputado = float(st["imputadoPorDia"].get(fecha, 0))
    restante = max(0.0, round(jornada - imputado, 2))

    pagos, resto_banco = [], []
    for e in st["bancoHoras"]:
        if restante <= 0:
            resto_banco.append(e)
            continue
        h = min(float(e["horas"]), restante)
        pagos.append({"task": e["task"], "issue": e["issueKey"], "horas": round(h, 2),
                      "origen": e.get("origen")})
        restante = round(restante - h, 2)
        sobra = round(float(e["horas"]) - h, 2)
        if sobra > 0:
            resto_banco.append({**e, "horas": sobra})  # re-banca lo que no cabe

    out = {"fecha": fecha, "jornada": jornada, "imputadoHoy": imputado,
           "pagos": pagos, "quedaEnBanco": round(sum(float(e["horas"]) for e in resto_banco), 2)}
    if args.apply and pagos:
        st["imputadoPorDia"][fecha] = round(imputado + sum(p["horas"] for p in pagos), 2)
        st["bancoHoras"] = resto_banco
        for p in pagos:
            t = st["tasks"].setdefault(p["task"], {})
            t.setdefault("issueKey", p["issue"])
            t["worklog"] = round(float(t.get("worklog", 0)) + p["horas"], 2)
        save_json(state_path(args), st)
        out["aplicado"] = True
    print(json.dumps(out, ensure_ascii=False))
    return 0


def cmd_status(args):
    st = load_state(args)
    print(json.dumps({"imputadoPorDia": st["imputadoPorDia"],
                      "bancoPendiente": round(sum(float(e["horas"]) for e in st["bancoHoras"]), 2),
                      "bancoHoras": st["bancoHoras"], "tareas": len(st["tasks"])},
                     ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Cálculo de worklog con tope diario y banco.")
    ap.add_argument("cmd", choices=["plan", "drain", "status"])
    ap.add_argument("--task"); ap.add_argument("--issue")
    for f in ("ia-real", "ia-est", "sup-real", "sup-est", "human-real", "human-est"):
        ap.add_argument("--" + f, type=float, dest=f.replace("-", "_"))
    ap.add_argument("--policy", choices=["banco", "parar", "seguir", "preguntar"])
    ap.add_argument("--fecha"); ap.add_argument("--apply", action="store_true")
    ap.add_argument("--state"); ap.add_argument("--rates"); ap.add_argument("--jira")
    args = ap.parse_args()
    if args.cmd == "plan":
        if not args.task or not args.issue:
            sys.exit("plan requiere --task y --issue")
        sys.exit(cmd_plan(args))
    sys.exit(cmd_drain(args) if args.cmd == "drain" else cmd_status(args))


if __name__ == "__main__":
    main()
