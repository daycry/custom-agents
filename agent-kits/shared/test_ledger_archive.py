#!/usr/bin/env python3
"""Tests de ledger-archive.py (archivado determinista de la historia cerrada del ledger). Ejecuta: pytest -q."""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "ledger-archive.py")
SLUG_DIR = "2026-01-01-demo"
FECHA = "2026-10-15"

CABECERA = """---
tasks: demo
estado: en-progreso
verificacion: obligatoria
---
# Checklist — demo

> **⚠️ Ledger canónico de progreso.** Fuente única de verdad.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Uno | 1 | {total} | x% |

## Fase 1 — Uno

### T-01 — Tarea uno

- **Estado**: en-progreso
- **Verificación**: {verif_t01}

**Criterios de aceptación**
- [ ] c1

### T-02 — Tarea dos

- **Estado**: completado
- **Verificación**: `pytest -q` → verde

**Criterios de aceptación**
- [x] c1
"""

TABLA = ("| # | Grado | Gap | Tarea | Corrección | Evidencia |\n"
         "|---|---|---|---|---|---|\n")

R1 = ("## Revisión de dos lentes — intento 1: Fase 1 (T-01) — un Important\n\n" +
      "Lentes A+B de contexto fresco sobre el diff de la fase; narrativa ya cerrada. " * 8 + "\n\n" +
      TABLA +
      "| 1 | Important | gap uno | T-01 | corregido en abc123 | test verde |\n\n")
R2 = ("## Revisión de dos lentes — intento 2: Fase 1 (T-01) — un gap pendiente\n\n" + TABLA +
      "| 1 | Important | gap dos | T-01 | pendiente | — |\n\n")
R3 = "## Revisión de dos lentes — intento 3: Fase 1 (T-01) — sin gaps\n\nSin gaps nuevos.\n\n"
RT2 = "## Revisión de dos lentes — intento 1: Fase 1 (T-02) — sin gaps\n\nLimpio.\n"


def ledger(verif_t01="`pytest -q` → verde"):
    return CABECERA.format(total=2, verif_t01=verif_t01) + "\n" + R1 + R2 + R3 + RT2


# Ledger con una ronda ANÓNIMA «sin gaps» que hereda las menciones de la sección anterior: si se
# quitara la anterior, la anónima heredaría de otra (o de nada) y la tarea perdería su cierre.
T03 = """
### T-03 — Tarea tres

- **Estado**: completado
- **Verificación**: `pytest -q` → verde

**Criterios de aceptación**
- [x] c1
"""
ANON_PREV = ("## Revisión de dos lentes — intento 1: Fase 1 — dos Minor\n\n" + TABLA +
             "| 1 | Minor | gap a | T-03 | corregido en def456 | test verde |\n\n")
ANON = "## Revisión de dos lentes — intento 2: sin gaps\n\n"


def ledger_anonimo():
    base = CABECERA.format(total=3, verif_t01="`pytest -q` → verde") + T03
    return base + "\n## Notas\n\nTexto.\n\n" + ANON_PREV + ANON + RT2


def _carpeta(tmp, texto, newline="\n"):
    carpeta = os.path.join(tmp, "docs", "roadmap", SLUG_DIR)
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, "tasks.md"), "wb") as fh:
        fh.write(texto.replace("\n", newline).encode("utf-8"))
    return carpeta


def run(carpeta, *extra):
    r = subprocess.run([sys.executable, SCRIPT, carpeta, "--fecha", FECHA, *extra],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout, r.stderr


def run_json(carpeta, *extra):
    code, out, err = run(carpeta, "--json", *extra)
    assert code == 0, (out, err)
    return json.loads(out)


def leer(path):
    with open(path, "rb") as fh:
        return fh.read()


def _lint_mod():
    spec = importlib.util.spec_from_file_location("ledger_lint_test_archive",
                                                  os.path.join(HERE, "ledger-lint.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def invariantes(mod, texto):
    secs = mod.secciones_revision(texto)
    tareas = {t["id"] for t in mod.parse_ledger(texto)["tareas"]}
    for s in secs:
        tareas |= mod.menciones(s)
    out = {}
    for t in sorted(tareas):
        intento, filas = mod.filas_pendientes_de_tarea(secs, t)
        out[t] = (intento, [(f["gap"], f["tarea"], f["grado"]) for f in filas],
                  mod.ultimo_intento_para(secs, [t]))
    out["__max__"] = max((s["intento"] for s in secs), default=None)
    return out


def test_en_seco_no_escribe_nada_y_propone_solo_el_intento_1():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger())
        antes = leer(os.path.join(carpeta, "tasks.md"))
        d = run_json(carpeta)
        assert d["aplicado"] is False
        assert [s["cabecera"] for s in d["secciones"]] == [R1.splitlines()[0][3:]]
        assert leer(os.path.join(carpeta, "tasks.md")) == antes
        assert not os.path.exists(os.path.join(carpeta, "execution-history.md"))
        assert d["bytes_despues"] < d["bytes_antes"] == len(antes)


def test_apply_archiva_solo_la_superada_y_deja_el_resto_con_motivo():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger())
        d = run_json(carpeta, "--apply")
        assert d["aplicado"] is True
        nuevo = leer(os.path.join(carpeta, "tasks.md")).decode("utf-8")
        assert "intento 1: Fase 1 (T-01)" not in nuevo.split("## Historial archivado")[0]
        for r in (R2, R3, RT2):
            assert r.splitlines()[0] in nuevo
        sha = hashlib.sha256(R1.encode("utf-8")).hexdigest()
        assert d["secciones"][0]["sha256"] == sha
        linea = (f"- {FECHA} · «Revisión de dos lentes — intento 1: Fase 1 (T-01) — un Important» → "
                 f"[execution-history.md](execution-history.md) · SHA-256 `{sha}`")
        assert nuevo.rstrip("\n").endswith("## Historial archivado\n\n" + linea), nuevo[-600:]
        motivos = {o["cabecera"][:45]: o["motivo"] for o in d["omitidas"]}
        assert len(d["omitidas"]) == 3, d["omitidas"]
        assert "pendiente" in motivos["Revisión de dos lentes — intento 2: Fase 1 (T"]
        assert "última" in motivos["Revisión de dos lentes — intento 1: Fase 1 (T"]
        assert "supera" in motivos["Revisión de dos lentes — intento 3: Fase 1 (T"]


def test_invariantes_y_ledger_lint_identicos_antes_y_despues():
    mod = _lint_mod()
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger())
        path = os.path.join(carpeta, "tasks.md")
        antes = leer(path).decode("utf-8")
        err_antes, _ = mod.lint(path)
        run_json(carpeta, "--apply")
        despues = leer(path).decode("utf-8")
        assert despues != antes
        assert invariantes(mod, despues) == invariantes(mod, antes)
        err_despues, avisos = mod.lint(path)
        assert len(err_despues) <= len(err_antes) == 0, err_despues
        assert not any("no casa con REVISION_HDR_PATTERN" in a for a in avisos), avisos


def test_historico_conserva_el_bloque_byte_a_byte_con_su_sha():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger())
        run_json(carpeta, "--apply")
        hist = leer(os.path.join(carpeta, "execution-history.md")).decode("utf-8")
        sha = hashlib.sha256(R1.encode("utf-8")).hexdigest()
        assert hist.startswith("# Historial de ejecución — demo\n")
        assert (f"## Archivado {FECHA} — Revisión de dos lentes — intento 1: Fase 1 (T-01) — un "
                f"Important (bytes sin cambios)") in hist
        assert f"SHA-256 del bloque: `{sha}`." in hist
        assert R1 in hist


def test_segunda_ejecucion_no_hace_nada_ni_duplica():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger())
        run_json(carpeta, "--apply")
        t1 = leer(os.path.join(carpeta, "tasks.md"))
        h1 = leer(os.path.join(carpeta, "execution-history.md"))
        d = run_json(carpeta, "--apply")
        assert d["secciones"] == [] and d["verificaciones"] == []
        assert leer(os.path.join(carpeta, "tasks.md")) == t1
        assert leer(os.path.join(carpeta, "execution-history.md")) == h1
        assert t1.decode("utf-8").count("## Historial archivado") == 1


def test_historico_que_ya_tiene_el_sha_no_se_duplica():
    """Corte entre las dos escrituras: el histórico ya se escribió y el ledger no."""
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger())
        sha = hashlib.sha256(R1.encode("utf-8")).hexdigest()
        previo = f"# Historial de ejecución — demo\n\n## Archivado previo\n\nSHA-256 del bloque: `{sha}`.\n\n{R1}"
        with open(os.path.join(carpeta, "execution-history.md"), "wb") as fh:
            fh.write(previo.encode("utf-8"))
        run_json(carpeta, "--apply")
        hist = leer(os.path.join(carpeta, "execution-history.md")).decode("utf-8")
        assert hist == previo
        nuevo = leer(os.path.join(carpeta, "tasks.md")).decode("utf-8")
        assert R1.splitlines()[0] not in nuevo and f"SHA-256 `{sha}`" in nuevo


def test_anonima_que_hereda_de_la_anterior_bloquea_su_archivado():
    mod = _lint_mod()
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger_anonimo())
        path = os.path.join(carpeta, "tasks.md")
        antes = leer(path).decode("utf-8")
        # precondición: la anónima es el cierre de T-03 POR HERENCIA
        assert mod.ultimo_intento_para(mod.secciones_revision(antes), ["T-03"]) == 2
        d = run_json(carpeta, "--apply")
        assert d["secciones"] == []
        motivos = {o["cabecera"]: o["motivo"] for o in d["omitidas"]}
        assert "invariante" in motivos[ANON_PREV.splitlines()[0][3:]], motivos
        assert leer(path).decode("utf-8") == antes


def test_cambio_de_herencia_sin_efecto_en_las_tareas_tambien_bloquea_y_es_idempotente():
    """Caso del ledger real (Bloque21 · ciclo correctivo): la ronda anónima hereda de la sección
    INMEDIATAMENTE anterior (T-02 intento 2); al quitarla heredaría de la de T-01 intento 5, y como
    T-01 y T-02 ya tienen intentos más altos y ninguna fila pendiente, ningún resultado POR TAREA
    cambia — pero la ronda pasaría a «cerrar» otra tarea, y en la siguiente ejecución aparecerían
    candidatas nuevas (no idempotente). No se archiva, y una segunda pasada no encuentra nada."""
    texto = (CABECERA.format(total=2, verif_t01="`pytest -q` → verde") + "\n"
             "## Revisión de dos lentes — intento 9: Fase 1 (T-02)\n\nCerrada.\n\n"
             "## Revisión de dos lentes — intento 5: Fase 1 (T-01)\n\nCerrada.\n\n"
             "## Revisión de dos lentes — intento 2: Fase 1 (T-02)\n\nCerrada.\n\n"
             "## Revisión de dos lentes — intento 3: sin gaps\n\n"
             "## Revisión de dos lentes — intento 1: Fase 1 (T-01) — cierre\n\nCerrada.\n")
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, texto)
        d = run_json(carpeta, "--apply")
        motivos = {o["cabecera"]: o["motivo"] for o in d["omitidas"]}
        assert "herencia" in motivos["Revisión de dos lentes — intento 2: Fase 1 (T-02)"], motivos
        t1 = leer(os.path.join(carpeta, "tasks.md"))
        assert run_json(carpeta, "--apply")["secciones"] == []
        assert leer(os.path.join(carpeta, "tasks.md")) == t1


def test_historico_con_finales_mezclados_no_se_reescribe():
    """El histórico real mezcla CRLF y LF: solo se AÑADE al final; lo previo queda byte a byte."""
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger())
        previo = "# Historial\r\n\r\nviejo CRLF\r\n\nviejo LF\nmás LF\n".encode("utf-8")
        with open(os.path.join(carpeta, "execution-history.md"), "wb") as fh:
            fh.write(previo)
        run_json(carpeta, "--apply")
        hist = leer(os.path.join(carpeta, "execution-history.md"))
        assert hist.startswith(previo)
        assert R1.encode("utf-8") in hist[len(previo):]       # LF dominante en lo añadido


def test_verificacion_posterior_que_empeora_no_escribe_y_sale_con_1(monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("ledger_archive_mut", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger())
        antes = leer(os.path.join(carpeta, "tasks.md"))
        reales = mod.errores_lint
        monkeypatch.setattr(mod, "errores_lint",
                            lambda data: reales(data) + ([] if data == antes else ["colada"]))
        assert mod.main([carpeta, "--apply", "--fecha", FECHA]) == 1
        assert "ledger-lint empeoraría" in capsys.readouterr().err
        assert leer(os.path.join(carpeta, "tasks.md")) == antes
        assert not os.path.exists(os.path.join(carpeta, "execution-history.md"))


def test_verificacion_larga_se_recorta_a_la_primera_frase_y_el_original_va_al_historico():
    mod = _lint_mod()
    larga = "Primera frase corta. " + "palabra " * 300
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger(verif_t01=larga.strip()))
        d = run_json(carpeta, "--apply")
        original = f"- **Verificación**: {larga.strip()}\n"
        sha = hashlib.sha256(original.encode("utf-8")).hexdigest()
        assert d["verificaciones"] == [{"tarea": "T-01", "sha256": sha,
                                        "bytes": len(original.encode("utf-8"))}]
        nuevo = leer(os.path.join(carpeta, "tasks.md")).decode("utf-8")
        esperado = ("- **Verificación**: Primera frase corta. Detalle archivado: "
                    f"[execution-history.md](execution-history.md) · SHA-256 `{sha[:12]}`.")
        assert esperado + "\n" in nuevo
        assert "- **Verificación**: `pytest -q` → verde" in nuevo     # la corta (T-02) no se toca
        hist = leer(os.path.join(carpeta, "execution-history.md")).decode("utf-8")
        assert original in hist and f"## Archivado {FECHA} — T-01 · Verificación (bytes sin cambios)" in hist
        errores, _ = mod.lint(os.path.join(carpeta, "tasks.md"))
        assert errores == []                                           # verificacion: obligatoria


def test_verificacion_sin_punto_se_corta_en_frontera_de_palabra_y_respeta_el_umbral():
    larga = ("abcdefghi " * 250).strip()
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger(verif_t01=larga))
        assert run_json(carpeta, "--verificacion-max", "5000")["verificaciones"] == []
        run_json(carpeta, "--apply")
        nuevo = leer(os.path.join(carpeta, "tasks.md")).decode("utf-8")
        campo = next(ln for ln in nuevo.splitlines() if ln.startswith("- **Verificación**: abc"))
        frase = campo[len("- **Verificación**: "):campo.index(" Detalle archivado:")]
        assert len(frase) <= 401 and re.fullmatch(r"(abcdefghi )*abcdefghi…?", frase), frase


def test_crlf_se_conserva():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger(), newline="\r\n")
        run_json(carpeta, "--apply")
        for nombre in ("tasks.md", "execution-history.md"):
            datos = leer(os.path.join(carpeta, nombre))
            assert b"\r\n" in datos and datos.count(b"\n") == datos.count(b"\r\n"), nombre
        hist = leer(os.path.join(carpeta, "execution-history.md"))
        assert R1.replace("\n", "\r\n").encode("utf-8") in hist


def test_carpeta_sin_tasks_md_es_error_de_uso():
    with tempfile.TemporaryDirectory() as tmp:
        code, out, err = run(tmp)
        assert code == 2, (out, err)
        assert "tasks.md" in err


def test_salida_legible_resume_bytes():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger())
        code, out, _ = run(carpeta)
        assert code == 0
        assert "en seco" in out and "bytes" in out and "intento 1: Fase 1 (T-01)" in out


# ----------------------------------------------------------------- (D) Notas largas ----

NOTA_LARGA = "Primera frase de la nota. " + "detalle largo " * 80
NOTA_CORTA = "nota corta que se queda tal cual."


def ledger_notas(estado_t01="completado", nota_t01=NOTA_LARGA, nota_t02=NOTA_CORTA):
    hechas = 2 if estado_t01 == "completado" else 1
    return f"""---
tasks: demo
estado: en-progreso
---
# Checklist — demo

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Uno | {hechas} | 2 | x% |

## Fase 1 — Uno

### T-01 — Tarea uno

- **Estado**: {estado_t01}
- **Verificación**: `pytest -q` → verde

**Criterios de aceptación**
- [{'x' if estado_t01 == 'completado' else ' '}] c1

**Notas**: {nota_t01}

### T-02 — Tarea dos

- **Estado**: completado
- **Verificación**: `pytest -q` → verde

**Criterios de aceptación**
- [x] c1

**Notas**: {nota_t02}

## Notas finales

Texto libre del ledger que no es una Nota de tarea.
"""


def test_nota_larga_de_tarea_completada_se_recorta_con_puntero_y_sha():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger_notas())
        d = run_json(carpeta, "--apply")
        original = f"**Notas**: {NOTA_LARGA}\n"
        sha = hashlib.sha256(original.encode("utf-8")).hexdigest()
        assert d["notas"] == [{"tarea": "T-01", "sha256": sha,
                               "bytes": len(original.encode("utf-8"))}]
        nuevo = leer(os.path.join(carpeta, "tasks.md")).decode("utf-8")
        esperado = ("**Notas**: Primera frase de la nota. Detalle archivado: "
                    f"[execution-history.md](execution-history.md) · SHA-256 `{sha[:12]}`.")
        assert esperado + "\n" in nuevo
        assert f"**Notas**: {NOTA_CORTA}\n" in nuevo                 # la corta no se toca
        assert "Texto libre del ledger que no es una Nota de tarea." in nuevo
        hist = leer(os.path.join(carpeta, "execution-history.md")).decode("utf-8")
        assert original in hist and f"## Archivado {FECHA} — T-01 · Notas (bytes sin cambios)" in hist
        assert f"SHA-256 del bloque: `{sha}`." in hist
        errores, _ = _lint_mod().lint(os.path.join(carpeta, "tasks.md"))
        assert errores == []


def test_nota_de_tarea_no_completada_queda_intacta():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger_notas(estado_t01="en-progreso"))
        antes = leer(os.path.join(carpeta, "tasks.md"))
        assert run_json(carpeta, "--apply")["notas"] == []
        assert leer(os.path.join(carpeta, "tasks.md")) == antes
        assert not os.path.exists(os.path.join(carpeta, "execution-history.md"))


def test_notas_segunda_ejecucion_no_archiva_nada_ni_duplica():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger_notas())
        run_json(carpeta, "--apply")
        t1 = leer(os.path.join(carpeta, "tasks.md"))
        h1 = leer(os.path.join(carpeta, "execution-history.md"))
        d = run_json(carpeta, "--apply")
        assert d["notas"] == [] and d["aplicado"] is False
        assert leer(os.path.join(carpeta, "tasks.md")) == t1
        assert leer(os.path.join(carpeta, "execution-history.md")) == h1


def test_notas_max_es_configurable():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger_notas())
        assert run_json(carpeta, "--notas-max", "5000")["notas"] == []
        assert [n["tarea"] for n in run_json(carpeta, "--notas-max", "20")["notas"]] == ["T-01", "T-02"]


def test_notas_crlf_se_conserva():
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger_notas(), newline="\r\n")
        run_json(carpeta, "--apply")
        for nombre in ("tasks.md", "execution-history.md"):
            datos = leer(os.path.join(carpeta, nombre))
            assert datos.count(b"\n") == datos.count(b"\r\n") > 0, nombre
        hist = leer(os.path.join(carpeta, "execution-history.md"))
        assert f"**Notas**: {NOTA_LARGA}\r\n".encode("utf-8") in hist


def test_notas_con_verificacion_posterior_que_falla_no_escribe_y_sale_con_1(monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("ledger_archive_mut2", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger_notas())
        antes = leer(os.path.join(carpeta, "tasks.md"))
        reales = mod.errores_lint
        monkeypatch.setattr(mod, "errores_lint",
                            lambda data: reales(data) + ([] if data == antes else ["colada"]))
        assert mod.main([carpeta, "--apply", "--fecha", FECHA]) == 1
        assert "ledger-lint empeoraría" in capsys.readouterr().err
        assert leer(os.path.join(carpeta, "tasks.md")) == antes
        assert not os.path.exists(os.path.join(carpeta, "execution-history.md"))


def test_nota_dentro_de_valla_de_codigo_no_se_toca():
    nota = "corta.\n\n```\n**Notas**: " + NOTA_LARGA + "\n```"
    with tempfile.TemporaryDirectory() as tmp:
        carpeta = _carpeta(tmp, ledger_notas(nota_t01="ejemplo corto", nota_t02=nota))
        assert run_json(carpeta, "--apply")["notas"] == []
