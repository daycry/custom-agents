"""Regression checks for the category contract's documentation consumers."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_A2_curator_contract_and_catalog_descriptions_expose_new_fields():
    for name in ('docs/agents/knowledge-curator.md', 'agent-kits/knowledge-curator/README.md'):
        text = (ROOT / name).read_text(encoding='utf-8')
        for field in ('allowed_producers', 'required_metadata', 'required_sections', 'content_origin', 'proposed_by'):
            assert field in text, (name, field)
    catalog = (ROOT / 'CLAUDE.md').read_text(encoding='utf-8')
    assert '`knowledge-category-template`' in catalog
    assert '`/knowledge-category-check`' in catalog


def test_A3_category_index_links_resolve_to_existing_workflow_headings():
    for name in ('docs/README.md', 'docs/en/README.md'):
        source = ROOT / name
        links = re.findall(r'\]\((guides/knowledge-categories\.md#[^)]+)\)', source.read_text(encoding='utf-8'))
        assert links, name
        for link in links:
            path, anchor = link.split('#')
            headings = re.findall(r'^#+ (.+)$', (source.parent / path).read_text(encoding='utf-8'), re.M)
            anchors = {re.sub(r'[^\w\s-]', '', heading.lower()).replace(' ', '-') for heading in headings}
            assert anchor in anchors, (name, link)
    for name in ('docs/FLOWS.md', 'docs/en/FLOWS.md'):
        source = ROOT / name
        text = source.read_text(encoding='utf-8')
        match = re.search(r'W-(\d+)[^\n]*?W-(\d+)\]\(guides/dashboard.md\)', text)
        assert match, name
        dashboard = (source.parent / 'guides/dashboard.md').read_text(encoding='utf-8')
        actual = {int(n) for n in re.findall(r'^## W-(\d+)[.] ', dashboard, re.M)}
        assert set(range(int(match[1]), int(match[2]) + 1)) <= actual, name
