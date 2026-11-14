"""Los plazos de pared se INYECTAN, no se esperan (T-23 fix9, gaps 2 y 5 del intento 9; doctrina de fix5, punto 7).

Un test que asserta `dur_ms < 5000` o `recuperadas == 3` con el reloj de la maquina falla bajo carga (el replay del journal
fallo 5 de 7 ejecuciones en serie). Estos tests vigilan que no vuelva: sin asercion de duracion por reloj de pared en
`test_journal.py` y con el plazo del servidor del panel inyectado en las dos pruebas que abren una revision con el dueno real.
"""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "agent-kits" / "shared" / "test_journal.py"
PANEL = ROOT / "tests" / "test_panel_review_panel_server.py"

# `assert dur_ms < 5000`, `assert elapsed < 1.5`, `assert dt < 12`: una cota de reloj de pared sobre una duracion medida.
PARED_RE = re.compile(r"^\s*assert\s+(?:dur_ms|elapsed|dt|duracion|tardo)\w*\s*<", re.M)


def test_test_journal_no_asserta_duraciones_de_pared():
    hallazgos = [(texto.count("\n", 0, m.start()) + 1, m.group(0).strip())
                 for texto in [JOURNAL.read_text(encoding="utf-8")] for m in PARED_RE.finditer(texto)]
    assert not hallazgos, f"aserciones de reloj de pared en test_journal.py (linea, texto): {hallazgos}"


def _prueba(arbol, nombre_prefijo):
    return next(n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef) and n.name.startswith(nombre_prefijo))


def test_las_dos_pruebas_del_panel_con_el_dueno_real_inyectan_el_plazo_y_van_en_paralelo():
    texto = PANEL.read_text(encoding="utf-8")
    arbol = ast.parse(texto)
    for prefijo in ("test_real_owner_open_then_summary_and_current",
                    "test_con_el_dueno_real_refresh_y_submit_se_ven_al_instante"):
        funcion = _prueba(arbol, prefijo)
        decoradores = [ast.unparse(d) for d in funcion.decorator_list]
        assert not any("serie" in d for d in decoradores), f"{prefijo}: sigue en el paso serie ({decoradores})"
        cuerpo = ast.get_source_segment(texto, funcion)
        assert "BODY_TIMEOUT" in cuerpo and "monkeypatch" in [a.arg for a in funcion.args.args], \
            f"{prefijo}: no inyecta BODY_TIMEOUT con monkeypatch"


# --- fix10, gap 7: los presupuestos cortos no dependen de la carga de la maquina -----------------------------------------------
# Un `budget_ms` constante por debajo de 1 s con el reloj real se agota si la maquina va cargada (la pasada se corta antes de
# su primer elemento). Un test que lo usa congela el reloj (`_reloj_congelado`) o comprueba que el cerrojo esta ocupado (el
# presupuesto solo acota la espera y la asercion es tolerante). Un test nuevo con presupuesto corto y reloj real falla aqui.
PRESUPUESTO_CORTO_CERROJO = {
    "test_replay_termina_dentro_del_presupuesto_con_0_10_100_pendientes",
    "test_replay_cerrojo_ocupado_bajo_presupuesto_devuelve_bloqueado_rapido",
    "test_replay_sigue_bloqueado_si_el_cerrojo_esta_realmente_ocupado",
    "test_recover_cerrojo_ocupado_bajo_presupuesto_devuelve_bloqueado_rapido",
    "test_replay_con_recover_bloqueado_inicializa_recuperadas_y_candidatas",
}


def test_los_presupuestos_cortos_de_test_journal_no_dependen_del_reloj_de_pared():
    arbol = ast.parse(JOURNAL.read_text(encoding="utf-8"))
    sin_reloj = []
    for f in ast.walk(arbol):
        if not (isinstance(f, ast.FunctionDef) and f.name.startswith("test_")) or f.name in PRESUPUESTO_CORTO_CERROJO:
            continue
        cortos = [c for c in ast.walk(f) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
                  and c.func.attr in ("replay", "recover")
                  and any(k.arg == "budget_ms" and isinstance(k.value, ast.Constant) and isinstance(k.value.value, int)
                          and 0 < k.value.value < 1000 for k in c.keywords)]
        congela = any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "_reloj_congelado"
                      for c in ast.walk(f))
        if cortos and not congela:
            sin_reloj.append(f.name)
    assert not sin_reloj, f"presupuesto corto con reloj real (usa `_reloj_congelado(monkeypatch)`): {sin_reloj}"
