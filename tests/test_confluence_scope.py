#!/usr/bin/env python3
"""Tests de confluence-scope.py (verificador + staging de la política de
Confluence). Ejecuta: python3 tests/test_confluence_scope.py

Cubre CA-07 (--status), CA-08 (--check), CA-10 (--stage, idempotencia) y
CA-11 (mapeo inverso staged->canónico), con fixtures propias (sin red, sin
conector). Cada [GWT] tiene un test que lo ejerce de verdad, no un
`assert True`.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "confluence-publish" / "scripts" / "confluence-scope.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "confluence-scope"
HOOK = ROOT / "hooks" / "mark-docs-pending.sh"

# Carga el script como módulo (el nombre lleva guiones: no es un identificador
# válido para `import`, así que se resuelve con importlib.util).
_spec = importlib.util.spec_from_file_location("confluence_scope", SCRIPT)
cs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cs)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fresh_root(tmp):
    """Copia la fixture a un directorio temporal (los tests que hacen
    --stage o tocan ficheros no deben mutar la fixture compartida)."""
    dst = Path(tmp) / "proj"
    shutil.copytree(FIXTURE, dst)
    return dst


def run(args, cwd=None):
    r = subprocess.run([sys.executable, str(SCRIPT)] + args,
                        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)
    return r.returncode, r.stdout, r.stderr


def test_glob_to_regex():
    # '**' de directorios también matchea CERO directorios (semántica de
    # glob.glob(..., recursive=True)) — el caso que rompería una
    # implementación ingenua basada en fnmatch puro.
    assert cs.glob_match("docs/**/atlassian-connector-notes.md", "docs/atlassian-connector-notes.md")
    assert cs.glob_match("docs/**/atlassian-connector-notes.md", "docs/sub/atlassian-connector-notes.md")
    assert cs.glob_match("docs/roadmap/**/tasks.md", "docs/roadmap/init1/tasks.md")
    assert not cs.glob_match("docs/roadmap/**/tasks.md", "docs/roadmap/init1/spec.md")
    assert cs.glob_match("**/testing/**", "docs/roadmap/init1/testing/report.md")
    assert cs.glob_match("**/*.md", "docs/README.md")
    assert cs.glob_match("**/*.md", "docs/roadmap/init1/spec.md")
    assert not cs.glob_match("docs/security-scan/**", "docs/README.md")
    print("test_glob_to_regex: OK")


def test_check_ok_with_good_config():
    code, out, _ = run(["--check", "--root", str(FIXTURE), "--config", str(FIXTURE / "confluence.json")])
    assert code == 0, out
    assert "OK" in out
    print("test_check_ok_with_good_config: OK")


def test_check_fails_without_security_scan():
    # CA-08 [GWT]: exclude que omite docs/security-scan/** -> exit != 0 y
    # el mensaje NOMBRA la invariante violada.
    code, out, _ = run(["--check", "--root", str(FIXTURE), "--config", str(FIXTURE / "confluence-bad.json")])
    assert code == 1, out
    assert "docs/security-scan" in out, out
    print("test_check_fails_without_security_scan: OK")


def test_check_degrades_to_defaults_without_project_config():
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        (proj / "confluence.json").unlink()
        (proj / "confluence-bad.json").unlink()
        code, out, _ = run(["--check", "--root", str(proj)])
        assert code == 0, out
        assert "defaults" in out, out
    print("test_check_degrades_to_defaults_without_project_config: OK")


def test_check_explicit_missing_config_is_an_error():
    # gap I3: pedir --config a un fichero que NO existe no puede degradar en
    # silencio a los defaults (eso ocultaría que nadie validó nada real).
    code, out, err = run(["--check", "--root", str(FIXTURE), "--config", str(FIXTURE / "no-existe.json")])
    assert code != 0, (code, out, err)
    assert "no existe" in (out + err), (out, err)
    print("test_check_explicit_missing_config_is_an_error: OK")


def test_check_explicit_corrupt_config_is_an_error():
    # gap I3: idem con JSON corrupto en la ruta pedida explícitamente.
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "roto.json"
        bad.write_text("{ esto no es json", encoding="utf-8")
        code, out, err = run(["--check", "--root", str(FIXTURE), "--config", str(bad)])
        assert code != 0, (code, out, err)
        assert "no es JSON" in (out + err) or "válido" in (out + err), (out, err)
    print("test_check_explicit_corrupt_config_is_an_error: OK")


def test_status_categories_and_scope():
    # CA-07 [GWT]: clasifica en las 4 categorías, lista los excluidos
    # esperados y no lista nada fuera de docs/, con exit 0.
    code, out, _ = run(["--status", "--root", str(FIXTURE), "--config", str(FIXTURE / "confluence.json")])
    assert code == 0, out
    for pat in ("docs/en/**", "docs/examples/**", "docs/agents/**", "**/testing/**", "docs/security-scan/**",
                "docs/knowledge/journal/**"):
        assert pat in out, f"falta el patrón {pat!r} en la salida:\n{out}"
    for rel in ("docs/en/README.md", "docs/examples/foo/README.md", "docs/agents/bar.md",
                "docs/security-scan/finding.md", "docs/roadmap/init1/testing/report.md",
                "docs/roadmap/init1/tasks.md", "docs/knowledge/journal/2026-01-01-demo.md"):
        assert rel in out, f"falta {rel!r} entre los excluidos:\n{out}"
    for rel in ("docs/README.md", "docs/roadmap/init1/spec.md"):
        assert rel in out, f"falta {rel!r} en alcance:\n{out}"
    # parity-core: design.md (agente architect) es DECISIÓN de arquitectura → se publica (no está en exclude)
    design_lines = [line for line in out.splitlines() if "docs/roadmap/init1/design.md" in line]
    assert design_lines, f"falta docs/roadmap/init1/design.md en la salida:\n{out}"
    assert all("[excluido:" not in line for line in design_lines), (
        f"design.md aparece excluido (debe publicarse como spec.md):\n{design_lines}")
    # T-16 (knowledge-capture): docs/knowledge/** NO está en el exclude, así que
    # un fichero de ejemplo bajo esa carpeta debe aparecer EN ALCANCE (pendiente,
    # no excluido) -- no un assert True, se comprueba la clasificación real.
    assert "docs/knowledge/README.md" in out, f"falta docs/knowledge/README.md en alcance:\n{out}"
    knowledge_lines = [line for line in out.splitlines() if "docs/knowledge/README.md" in line]
    assert knowledge_lines, f"docs/knowledge/README.md no aparece en ninguna línea:\n{out}"
    # memory-health: el journal de sesión (bitácora, no decisión) SÍ está excluido aunque viva en docs/knowledge/
    journal_lines = [line for line in out.splitlines() if "docs/knowledge/journal/2026-01-01-demo.md" in line]
    assert journal_lines and all("[excluido:" in line for line in journal_lines), (
        f"docs/knowledge/journal/** debe aparecer EXCLUIDO:\n{journal_lines}")
    assert all("[excluido:" not in line for line in knowledge_lines), (
        f"docs/knowledge/README.md aparece excluido (no debería):\n{knowledge_lines}")
    # knowledge-split: el subárbol docs/knowledge/gotchas/ (un fichero por entrada)
    # entra en alcance igual que el resto de docs/knowledge/** -- no un aserto vacío,
    # se comprueba la clasificación real de un fichero dentro de la subcarpeta.
    assert "docs/knowledge/gotchas/ejemplo.md" in out, (
        f"falta docs/knowledge/gotchas/ejemplo.md en alcance:\n{out}")
    gotchas_lines = [line for line in out.splitlines() if "docs/knowledge/gotchas/ejemplo.md" in line]
    assert gotchas_lines, f"docs/knowledge/gotchas/ejemplo.md no aparece en ninguna línea:\n{out}"
    assert all("[excluido:" not in line for line in gotchas_lines), (
        f"docs/knowledge/gotchas/ejemplo.md aparece excluido (no debería):\n{gotchas_lines}")
    # nada fuera de docs/: cada línea de fichero listada empieza por 'docs/'
    for line in out.splitlines():
        if "]" in line and ("[pendiente]" in line or "[sincronizado]" in line
                             or "[desactualizado]" in line or "[excluido:" in line):
            path_part = line.rsplit(" ", 1)[-1]
            assert path_part.startswith("docs/"), f"fichero fuera de docs/: {line}"
    print("test_status_categories_and_scope: OK")


def test_status_sync_classification():
    # pendiente / desactualizado / sincronizado, cruzando con el manifiesto.
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        readme = proj / "docs" / "README.md"
        state = {
            "docs/README.md": {"hash": sha256_text(readme.read_text(encoding="utf-8")), "pageId": "1"},
            "docs/roadmap/init1/spec.md": {"hash": "0" * 64, "pageId": "2"},
            # docs/roadmap/init1/... no tiene entrada equivalente para todo -> el resto sale pendiente
        }
        state_path = proj / "confluence-state.json"
        state_path.write_text(json.dumps(state), encoding="utf-8")
        code, out, _ = run(["--status", "--root", str(proj), "--config", str(proj / "confluence.json"),
                             "--state", str(state_path)])
        assert code == 0, out
        assert "[sincronizado] docs/README.md" in out, out
        assert "[desactualizado] docs/roadmap/init1/spec.md" in out, out
    print("test_status_sync_classification: OK")


def test_status_without_manifest_all_pending():
    code, out, _ = run(["--status", "--root", str(FIXTURE), "--config", str(FIXTURE / "confluence.json"),
                         "--state", str(FIXTURE / "no-existe.json")])
    assert code == 0, out
    assert "[pendiente] docs/README.md" in out, out
    assert "[pendiente] docs/roadmap/init1/spec.md" in out, out
    print("test_status_without_manifest_all_pending: OK")


def test_stage_creates_exact_scope_and_marker():
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        code, out, _ = run(["--stage", "--root", str(proj), "--config", str(proj / "confluence.json")])
        assert code == 0, out
        out_dir = proj / "docs" / "confluence"
        staged = sorted(str(p.relative_to(out_dir)) for p in out_dir.rglob("*") if p.is_file())
        # exactamente los 4 en alcance (incluido docs/knowledge/README.md, T-16 de
        # knowledge-capture, y docs/knowledge/gotchas/ejemplo.md, knowledge-split)
        # + el marcador de staging (gap C1: NO se llama README.md, para no
        # colisionar/pisar la copia real)
        assert set(staged) == {
            cs.STAGE_MARKER_NAME, "README.md", "roadmap/init1/spec.md", "roadmap/init1/design.md",
            "knowledge/README.md", "knowledge/gotchas/ejemplo.md",
        }, staged   # design.md (architect) se publica como spec.md — parity-core
        assert (out_dir / cs.STAGE_MARKER_NAME).read_text(encoding="utf-8").startswith(
            f"# {cs.STAGE_MARKER_NAME} — carpeta GENERADA")
        # ningún excluido aparece dentro
        for bad in ("en", "examples", "agents", "security-scan"):
            assert not (out_dir / bad).exists(), f"{bad} no debería estar en el staging"
        assert not (out_dir / "roadmap" / "init1" / "tasks.md").exists()
        assert not (out_dir / "roadmap" / "init1" / "testing").exists()
        assert not (out_dir / "knowledge" / "journal").exists()          # bitácora fuera del staging (memory-health)
    print("test_stage_creates_exact_scope_and_marker: OK")


def test_stage_copies_readme_byte_for_byte():
    # gap C1: la copia de docs/README.md en el staging tiene que ser
    # BYTE A BYTE idéntica al canónico — nunca pisada por la plantilla de
    # aviso (que ahora vive aparte, en STAGE_MARKER_NAME).
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        canonical = (proj / "docs" / "README.md").read_bytes()
        code, out, _ = run(["--stage", "--root", str(proj), "--config", str(proj / "confluence.json")])
        assert code == 0, out
        staged = (proj / "docs" / "confluence" / "README.md").read_bytes()
        assert staged == canonical, "el README.md staged difiere del canónico (gap C1)"
    print("test_stage_copies_readme_byte_for_byte: OK")


def test_default_policy_excludes_staging_marker_from_publish_walk():
    # Revisión adversarial ronda 3 (gap importante): el paso 4 de SKILL.md
    # ("Árbol de docs") recorre `publish.source` (docs/confluence, el árbol
    # STAGED) respetando include/exclude — NO vuelve a invocar
    # confluence-scope.py, así que la autoexclusión por código de
    # `docs/confluence/**` (que solo protege el ESCANEO del canónico al
    # generar el staging) no cubre este segundo recorrido. Sin una entrada
    # explícita en `exclude`, el marcador se publicaría como página
    # boilerplate y quedaría huérfano en cada pull. No hay forma de
    # ejercer el paso 4 en sí con un script (lo ejecuta el agente siguiendo
    # la SKILL, no confluence-scope.py) — este test verifica la pieza
    # verificable por código: que la política POR DEFECTO ENVASADA
    # (`assets/confluence.example.json`, la misma que consumiría ese
    # recorrido) excluye el nombre reservado del marcador con el mismo
    # matcher de glob (`**`, semántica `glob.glob(recursive=True)`) que
    # usaría cualquier consumidor de esa config.
    default_publish, _ = cs.load_policy(str(ROOT))
    excludes = default_publish.get("exclude", [])
    assert any(cs.glob_match(p, cs.STAGE_MARKER_NAME) for p in excludes), (
        f"el exclude por defecto no cubre el marcador de staging "
        f"({cs.STAGE_MARKER_NAME}): {excludes}")
    # Y de verdad genera ese nombre exacto al hacer --stage (no un typo).
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        run(["--stage", "--root", str(proj), "--config", str(proj / "confluence.json")])
        assert (proj / "docs" / "confluence" / cs.STAGE_MARKER_NAME).is_file()
    print("test_default_policy_excludes_staging_marker_from_publish_walk: OK")


def test_stage_is_idempotent():
    # CA-10 [GWT]: dos ejecuciones seguidas sin cambios -> árbol idéntico.
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        cfg = str(proj / "confluence.json")
        run(["--stage", "--root", str(proj), "--config", cfg])
        out_dir = proj / "docs" / "confluence"

        def digest_tree():
            items = []
            for p in sorted(out_dir.rglob("*")):
                if p.is_file():
                    items.append((str(p.relative_to(out_dir)), hashlib.sha256(p.read_bytes()).hexdigest()))
            return items

        first = digest_tree()
        code, out, _ = run(["--stage", "--root", str(proj), "--config", cfg])
        assert code == 0, out
        second = digest_tree()
        assert first == second, f"el staging no es idempotente:\n{first}\nvs\n{second}"
    print("test_stage_is_idempotent: OK")


def test_stage_wipes_previous_contents():
    # el script borra por completo docs/confluence/ antes de regenerar, pero
    # SOLO cuando es reconocible como un staging propio (gap C2): con el
    # marcador presente, un residuo de una ejecución anterior no sobrevive.
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        out_dir = proj / "docs" / "confluence"
        out_dir.mkdir(parents=True)
        (out_dir / cs.STAGE_MARKER_NAME).write_text("staging viejo", encoding="utf-8")
        (out_dir / "residuo-viejo.md").write_text("obsoleto", encoding="utf-8")
        code, out, err = run(["--stage", "--root", str(proj), "--config", str(proj / "confluence.json")])
        assert code == 0, (out, err)
        assert not (out_dir / "residuo-viejo.md").exists()
    print("test_stage_wipes_previous_contents: OK")


def test_stage_refuses_unsafe_out_target():
    # gap C2: un --out no vacío que NO parece un staging propio (sin el
    # marcador) se rechaza SIN borrar nada — nunca un `shutil.rmtree` a
    # ciegas sobre un directorio ajeno (p. ej. un `docs/` real).
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        unsafe = proj / "docs"  # directorio real del proyecto, con contenido real
        code, out, err = run(["--stage", "--root", str(proj), "--config", str(proj / "confluence.json"),
                               "--out", str(unsafe)])
        assert code != 0, (out, err)
        assert (unsafe / "README.md").is_file(), "el --out inseguro se ha tocado (gap C2)"
        assert (unsafe / "roadmap").exists(), "el --out inseguro se ha tocado (gap C2)"
    print("test_stage_refuses_unsafe_out_target: OK")


def test_stage_custom_out_survives_repeated_runs():
    # gap I2: la autoexclusión de la carpeta de salida se deriva del --out
    # EFECTIVO, no de un literal 'docs/confluence' cableado — un --out no
    # default anidado bajo docs/ no debe romperse en la segunda ejecución.
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        custom_out = proj / "docs" / "staged"
        cfg = str(proj / "confluence.json")
        code1, out1, err1 = run(["--stage", "--root", str(proj), "--config", cfg, "--out", str(custom_out)])
        assert code1 == 0, (out1, err1)
        code2, out2, err2 = run(["--stage", "--root", str(proj), "--config", cfg, "--out", str(custom_out)])
        assert code2 == 0, (out2, err2)
        assert (custom_out / cs.STAGE_MARKER_NAME).is_file()
        assert (custom_out / "roadmap" / "init1" / "spec.md").is_file()
    print("test_stage_custom_out_survives_repeated_runs: OK")


def test_out_relative_anchors_to_root_not_cwd():
    # Revisión adversarial ronda 3 (gap menor): --out relativo se resuelve
    # contra --root, NUNCA contra el cwd — al revés que --config/--state.
    # Caso ambiguo reproducido literalmente: desde un cwd distinto de
    # --root, pedir "--root demo --out demo/docs" (un --out ya prefijado
    # con el propio --root, error fácil de cometer) tiene que anidar
    # exactamente en demo/demo/docs — la resolución DOCUMENTADA, no una
    # ubicación sorpresa relativa al cwd (que habría sido <cwd>/demo/docs,
    # pisando/rozando el propio --root).
    with tempfile.TemporaryDirectory() as tmp:
        cwd = Path(tmp)
        shutil.copytree(FIXTURE, cwd / "demo")
        cfg = "demo/confluence.json"  # --config SÍ es relativo al cwd (a propósito, por contraste)
        code, out, err = run(["--stage", "--root", "demo", "--config", cfg, "--out", "demo/docs"], cwd=str(cwd))
        assert code == 0, (out, err)
        documented = cwd / "demo" / "demo" / "docs"  # --root='demo' + --out='demo/docs' anidado
        surprise_cwd_relative = cwd / "demo" / "docs"  # lo que daría un --out relativo al cwd
        assert (documented / cs.STAGE_MARKER_NAME).is_file(), \
            f"la resolución documentada (root-relative) no se cumplió: {documented}"
        assert not (surprise_cwd_relative / cs.STAGE_MARKER_NAME).is_file(), \
            f"--out se resolvió relativo al cwd, no a --root (contradice el --help): {surprise_cwd_relative}"
    print("test_out_relative_anchors_to_root_not_cwd: OK")


def test_map_inverse_resolves_canonical():
    # CA-11 [GWT]: con staging activo, el mapeo inverso resuelve al fichero
    # CANÓNICO, nunca a una ruta bajo docs/confluence/.
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        run(["--stage", "--root", str(proj), "--config", str(proj / "confluence.json")])
        code, out, _ = run(["--map", "docs/confluence/roadmap/init1/spec.md", "--root", str(proj)])
        assert code == 0, out
        canonical = out.strip()
        assert canonical == "docs/roadmap/init1/spec.md", canonical
        assert not canonical.startswith("docs/confluence/")
        assert (proj / canonical).is_file()
    print("test_map_inverse_resolves_canonical: OK")


def test_map_inverse_without_prior_stage_is_pure_arithmetic():
    # No requiere haber corrido --stage antes: es aritmética de rutas.
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        assert not (proj / "docs" / "confluence").exists()
        code, out, _ = run(["--map", "docs/confluence/README.md", "--root", str(proj)])
        assert code == 0, out
        assert out.strip() == "docs/README.md"
    print("test_map_inverse_without_prior_stage_is_pure_arithmetic: OK")


def test_map_orphan_page_is_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        run(["--stage", "--root", str(proj), "--config", str(proj / "confluence.json")])
        code, out, _ = run(["--map", "docs/confluence/no-existe.md", "--root", str(proj)])
        assert code == 1, out
        assert "huérfana" in out or "huerfana" in out, out
    print("test_map_orphan_page_is_rejected: OK")


def test_map_empty_argument_is_a_usage_error():
    # gap I4: '--map ""' NO puede salir 0 sin salida (una cadena vacía es
    # falsy en Python: el dispatch de main() tiene que distinguir "no se
    # pasó --map" de "se pasó --map con valor vacío").
    code, out, err = run(["--map", "", "--root", str(FIXTURE)])
    assert code != 0, (code, out, err)
    assert (out + err).strip() != "", "salida vacía junto con exit != 0: sin mensaje de error"
    print("test_map_empty_argument_is_a_usage_error: OK")


def test_map_out_outside_root_is_orphan_not_crash():
    # gap M1: --out fuera de --root no puede propagar un ValueError sin
    # capturar; se trata como página huérfana (exit 1), nunca un traceback.
    with tempfile.TemporaryDirectory() as tmp:
        proj = fresh_root(tmp)
        with tempfile.TemporaryDirectory() as other:
            outside = str(Path(other) / "staged-fuera")
            code, out, err = run(["--map", "README.md", "--root", str(proj), "--out", outside])
            assert code == 1, (code, out, err)
            assert "Traceback" not in err, err
            assert "huérfana" in out or "huerfana" in out, out
    print("test_map_out_outside_root_is_orphan_not_crash: OK")


def run_hook(file_path, project_dir):
    payload = json.dumps({"tool_input": {"file_path": file_path}})
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    r = subprocess.run(["bash", str(HOOK)], input=payload, capture_output=True,
                        text=True, encoding="utf-8", errors="replace", cwd=str(project_dir), env=env)
    return r.returncode, project_dir / ".claude" / ".confluence-pending"


def test_hook_ignores_staged_confluence_folder():
    # CA-12: editar bajo docs/confluence/** (carpeta STAGED) NO deja la marca
    # de pendiente — regenerar el staging no debe disparar otro --stage.
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp)
        (proj / ".claude").mkdir()
        code, marker = run_hook("docs/confluence/README.md", proj)
        assert code == 0
        assert not marker.exists(), "el hook dejo marca de pendiente para docs/confluence/**"
    print("test_hook_ignores_staged_confluence_folder: OK")


def test_hook_still_marks_pending_for_regular_docs():
    # regresión: un cambio normal bajo docs/ (fuera de security-scan y
    # confluence/) SIGUE dejando la marca, como antes de D5.
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp)
        (proj / ".claude").mkdir()
        code, marker = run_hook("docs/README.md", proj)
        assert code == 0
        assert marker.exists(), "el hook dejo de marcar docs/ normal como pendiente"
    print("test_hook_still_marks_pending_for_regular_docs: OK")


def test_hook_still_ignores_security_scan():
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp)
        (proj / ".claude").mkdir()
        code, marker = run_hook("docs/security-scan/finding.md", proj)
        assert code == 0
        assert not marker.exists(), "el hook dejo marca de pendiente para docs/security-scan/**"
    print("test_hook_still_ignores_security_scan: OK")


def main():
    tests = [
        test_glob_to_regex,
        test_check_ok_with_good_config,
        test_check_fails_without_security_scan,
        test_check_degrades_to_defaults_without_project_config,
        test_check_explicit_missing_config_is_an_error,
        test_check_explicit_corrupt_config_is_an_error,
        test_status_categories_and_scope,
        test_status_sync_classification,
        test_status_without_manifest_all_pending,
        test_stage_creates_exact_scope_and_marker,
        test_stage_copies_readme_byte_for_byte,
        test_default_policy_excludes_staging_marker_from_publish_walk,
        test_stage_is_idempotent,
        test_stage_wipes_previous_contents,
        test_stage_refuses_unsafe_out_target,
        test_stage_custom_out_survives_repeated_runs,
        test_out_relative_anchors_to_root_not_cwd,
        test_map_inverse_resolves_canonical,
        test_map_inverse_without_prior_stage_is_pure_arithmetic,
        test_map_orphan_page_is_rejected,
        test_map_empty_argument_is_a_usage_error,
        test_map_out_outside_root_is_orphan_not_crash,
        test_hook_ignores_staged_confluence_folder,
        test_hook_still_marks_pending_for_regular_docs,
        test_hook_still_ignores_security_scan,
    ]
    for t in tests:
        t()
    print(f"test_confluence_scope: {len(tests)}/{len(tests)} OK")


if __name__ == "__main__":
    main()
