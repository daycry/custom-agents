"""La implementación siempre se despacha a la identidad nativa `implementer` (auditoría H-6, H-7).

La guardia nativa (`agent-kits/shared/native-guardrail.py`) solo protege a las identidades de
`PROTECTED`: ni el hilo principal ni un subagente genérico la activan. Por eso el perfil `lite`
y el modo `subagentes: true` deben despachar la implementación al ID nativo del `implementer`.
"""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "commands/dev-cycle.md"
SUBAGENTS = ROOT / "agent-kits/dev-cycle/references/phase3-subagents.md"
ROLES = ROOT / "agent-kits/shared/native-roles.json"
TASK_BRIEF = ROOT / "agent-kits/shared/task-brief.py"
DOCS = [ROOT / p for p in ("docs/CONVENTIONS.md", "docs/en/CONVENTIONS.md",
                           "docs/FLOWS.md", "docs/en/FLOWS.md",
                           # revisión intento 1 (gap 4): también describían «lite en el hilo actual»
                           "docs/agents/implementer.md", "agent-kits/shared/README.md",
                           "docs/agents/CONTRACTS.md", "docs/guides/quality-playbook.md",
                           "docs/guides/subscription-efficiency.md",
                           # revisión intento 2 (A1): /setup también describía lite
                           "commands/setup.md")]


def _section(text, start, end_re=r"\n## "):
    i = text.index(start)
    m = re.compile(end_re).search(text, i + len(start))
    return text[i:m.start() if m else len(text)]


def test_implementer_es_identidad_protegida_en_todos_los_runtimes():
    spec = importlib.util.spec_from_file_location("native_guardrail", ROOT / "agent-kits/shared/native-guardrail.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert "implementer" in mod.PROTECTED
    runtimes = json.loads(ROLES.read_text(encoding="utf-8"))["runtimes"]
    for runtime in ("claude", "codex", "opencode"):
        assert runtimes[runtime]["implementer"].endswith("implementer"), runtime


def test_lite_despacha_al_implementer_nativo_en_secuencia():
    lite = _section(COMMAND.read_text(encoding="utf-8"), "## Perfil efectivo antes de despachar")
    plano = " ".join(lite.split())
    assert "hilo actual" not in plano, "lite no puede implementar en el hilo principal (sin guardia)"
    assert "`implementer`" in plano and "native-roles.json" in plano, plano
    assert "secuencia" in plano and "task-brief.py" in plano, plano


def test_subagentes_despachan_subagent_type_implementer_con_el_brief():
    texto = " ".join(SUBAGENTS.read_text(encoding="utf-8").split())
    paso2 = texto[texto.index("2. **Despacho brief-only**"):texto.index("3. **Estados de retorno**")]
    assert "subagent_type" in paso2 and "`implementer`" in paso2, paso2
    assert "native-roles.json" in paso2 and "brief" in paso2, paso2
    assert "genérico" in paso2, "debe prohibir expresamente el subagente genérico"
    paso4 = texto[texto.index("4. **Re-despacho acotado**"):texto.index("5. **Las puertas no cambian**")]
    assert "contexto principal" not in paso4, paso4
    assert "`implementer`" in paso4, paso4


def test_brief_lite_no_manda_implementar_en_el_hilo_actual():
    codigo = TASK_BRIEF.read_text(encoding="utf-8")
    assert "Implementa en el hilo actual" not in codigo
    assert "implementer" in codigo[codigo.index('"## Perfil lite"'):][:400]


def test_docs_describen_lite_con_implementer_nativo():
    for doc in DOCS:
        texto = " ".join(doc.read_text(encoding="utf-8").split())
        assert "hilo actual" not in texto and "current thread" not in texto, doc
        assert "implementer" in texto, doc


def test_respaldo_de_id_nativo_en_instalacion_copiada():
    """Revisión intento 1 (gap 11): con el bundle copiado en `.claude/agents/` el tipo es `implementer`."""
    for texto in (COMMAND.read_text(encoding="utf-8"), SUBAGENTS.read_text(encoding="utf-8")):
        plano = " ".join(texto.split())
        assert "copiad" in plano and "`implementer`" in plano, plano[:200]


def test_adaptadores_generados_conservan_el_despacho_nativo():
    spec = importlib.util.spec_from_file_location("dispatch_export", ROOT / "scripts/export-interop.py")
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    generated = exporter.generar(str(ROOT))
    codex = generated["interop/codex/command-skills/custom-agents-dev-cycle/references/command.md"]
    opencode = generated["interop/opencode/commands/dev-cycle.md"]
    for text in (codex, opencode):
        plano = " ".join(text.split())
        assert "hilo actual" not in plano and "native-roles.json" in plano


# --- Revisión intento 2: tests dedicados de los gaps de texto del intento 1 ---

def test_fix2_gap5_lens_select_doc_says_error_enables_c_and_d_in_auto():
    """Intento 1, gap 5: el docstring de review-lens-select y lens-c-heuristics ya no dicen «error → false»."""
    script = " ".join((ROOT / "skills/adversarial-review/scripts/review-lens-select.py").read_text(encoding="utf-8").split())
    heur = " ".join((ROOT / "skills/adversarial-review/references/lens-c-heuristics.md").read_text(encoding="utf-8").split())
    assert "ante error, aviso en stderr y ambas `false`" not in script
    assert "en modo `auto`, ambas `true`" in script
    assert "ante error avisa por stderr y devuelve `false`" not in heur
    assert "devuelve `true` en las Lentes C y D" in heur


def test_fix2_gap6_implementer_lists_name_every_denied_family():
    """Intento 1, gap 6 (y intento 2): las listas del implementer nombran todas las familias denegadas."""
    for rel in ("agents/implementer.md", "docs/agents/implementer.md"):
        texto = " ".join((ROOT / rel).read_text(encoding="utf-8").split())
        # Intento 3: la configuración pasa a LISTA BLANCA (se nombran las claves permitidas y `GIT_*`).
        for familia in ("git reset --hard", "git clean -f", "--mirror", "--prune", "git stash drop|clear",
                        "user.name", "core.quotepath", "color.*", "GIT_*", "git config", "update-ref"):
            assert familia in texto, (rel, familia)


def test_fix2_gap12_changelog_headers_carry_slug_for_changelog_sync():
    """Intento 1, gap 12: la cabecera de la fase lleva el slug entre acentos graves (idempotencia de changelog-sync)."""
    en = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    es = (ROOT / "CHANGELOG.es.md").read_text(encoding="utf-8")
    assert "### Fixed — `plugin-audit-remediation` initiative, phase 1" in en
    assert "### Fixed — iniciativa `plugin-audit-remediation`, fase 1" in es
    for texto in (en, es):
        assert texto.index("`plugin-audit-remediation`") < texto.index("## [3.2.3]")


def test_fix2_changelog_de_fase_1_recoge_los_cambios_del_intento_2():
    """Revisión intento 2 (documentación): la entrada ES/EN nombra exit 3, ⚠️ de doctor,
    la inyección de configuración git y NoDefaultCurrentDirectoryInExePath."""
    for rel in ("CHANGELOG.md", "CHANGELOG.es.md"):
        texto = (ROOT / rel).read_text(encoding="utf-8")
        seccion = texto[texto.index("`plugin-audit-remediation`"):texto.index("## [3.2.3]")]
        for marca in ("exit 3", "`/doctor`", "⚠️", "`GIT_CONFIG_*`", "`include.*`",
                      "NoDefaultCurrentDirectoryInExePath"):
            assert marca in seccion, (rel, marca)


def test_fix3_changelog_describe_la_lista_blanca_y_el_limite():
    """Revisión intento 3: la entrada de la Fase 1 describe la lista blanca de configuración git."""
    for rel, marca in (("CHANGELOG.md", "allowlist"), ("CHANGELOG.es.md", "lista blanca")):
        texto = (ROOT / rel).read_text(encoding="utf-8")
        seccion = texto[texto.index("`plugin-audit-remediation`"):texto.index("## [3.2.3]")]
        assert marca in seccion and "sandbox" in seccion and "`commit.gpgsign`" in seccion, rel


def test_fix3b_changelog_y_docs_dicen_que_commit_gpgsign_solo_vale_verdadero():
    """Revisión fix3b: la lista blanca publicada aclara que `commit.gpgsign` solo se permite a verdadero."""
    for rel, marca in (("CHANGELOG.md", "only set to true"), ("CHANGELOG.es.md", "solo a verdadero"),
                       ("agents/implementer.md", "solo a verdadero"), ("docs/agents/implementer.md", "solo a verdadero"),
                       ("docs/FLOWS.md", "solo a verdadero"), ("docs/en/FLOWS.md", "only set to true")):
        assert "`commit.gpgsign` (" + marca + ")" in (ROOT / rel).read_text(encoding="utf-8"), rel

