"""Named regressions for incorrect capabilities previously advertised in handbooks.

These checks preserve the two reviewed corrections; they do not claim to validate
all provider documentation or the semantics of arbitrary natural-language prose.
"""
from pathlib import Path
import hashlib
import json

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_B1_codex_cli_effort_uses_documented_model_command():
    """B1: do not recommend another surface's /reasoning as a CLI command."""
    source = (ROOT / "docs/guides/subscription-efficiency.md").read_text(encoding="utf-8")
    row = next(line for line in source.splitlines() if line.startswith("| Ajustar esfuerzo |"))
    codex_cell = row.split("|")[3]
    assert "`/reasoning`" not in codex_cell
    assert "`/model`" in codex_cell
    assert "--reasoning=high" in codex_cell


def test_B2_api_contract_is_not_presented_as_response_validation():
    """B2: a valid spec alone does not prove implementation conformance."""
    source = (ROOT / "docs/guides/quality-playbook.md").read_text(encoding="utf-8")
    row = next(line for line in source.splitlines() if line.startswith("| `api-contract` |"))
    assert "Contrastar una implementación" not in row
    assert "Validar specs OpenAPI" in row
    assert "cambios incompatibles entre versiones" in row


@pytest.mark.parametrize("source_name,pdf_name", [
    ("subscription-efficiency", "guia-uso-eficiente-claude-codex"),
    ("quality-playbook", "guia-resultados-calidad-custom-agents"),
])
def test_handbook_pdf_matches_its_markdown_edition(source_name, pdf_name):
    """An edited Markdown or PDF must not silently keep an old edition receipt."""
    source = ROOT / "docs/guides" / f"{source_name}.md"
    pdf = ROOT / "output/pdf" / f"{pdf_name}.pdf"
    manifest = json.loads(pdf.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    assert manifest["source_hash_method"] == "sha256-utf8-lf"
    assert manifest["pdf"] == pdf.relative_to(ROOT).as_posix()
    assert manifest["sources"] == {
        source.relative_to(ROOT).as_posix(): hashlib.sha256(
            source.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
    }
    assert manifest["pdf_sha256"] == hashlib.sha256(pdf.read_bytes()).hexdigest()
