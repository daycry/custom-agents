"""Audit minors (T-21): documentation that drifted from the code, and shipped pieces citing paths that do not ship."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def text(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def test_lens_d_is_named_where_the_review_lenses_are_listed():
    claude = text('CLAUDE.md')
    reviewer = next(l for l in claude.splitlines() if l.startswith('| **reviewer** |'))
    assert 'A/B/C/D' in reviewer
    skill_row = next(l for l in claude.splitlines() if l.startswith('| `adversarial-review` |'))
    assert 'D rendimiento' in skill_row or 'D (rendimiento)' in skill_row or 'lente D' in skill_row.lower()
    flat = lambda rel: ' '.join(text(rel).split())
    assert '**D** (rendimiento)' in flat('commands/dev-cycle.md')
    quick = flat('skills/quick-implement/SKILL.md')
    assert 'D (rendimiento)' in quick or 'lente D' in quick.lower()


def test_claude_md_states_the_global_guard_of_adr_023():
    claude = ' '.join(text('CLAUDE.md').split())
    assert 'ADR-023' in claude and 'guardia global' in claude
    assert 'un deny solo vive en el frontmatter' not in claude


def test_claude_md_distinguishes_the_console_from_the_static_panel():
    claude = text('CLAUDE.md')
    row = next(l for l in claude.splitlines() if l.startswith('| `/plugin-catalog` |'))
    assert 'consola' in row.lower() and '--serve' in row and 'control_center' in row
    skill = next(l for l in claude.splitlines() if l.startswith('| `plugin-panel` |'))
    assert 'consola' in skill.lower()


def test_shipped_pieces_do_not_cite_memory_paths_that_do_not_ship():
    """`docs/knowledge/` is the development record of this repo and is not in the npm payload."""
    offenders = []
    roots = [ROOT / 'agents', ROOT / 'commands', ROOT / 'skills', ROOT / 'agent-kits']
    for base in roots:
        for path in base.rglob('*.md'):
            body = path.read_text(encoding='utf-8')
            # concrete record files of THIS repo's memory (ADR-012-…, LES-010-…); the consumer's own
            # layout (`docs/knowledge/approved/`, globs) is legitimate and not matched
            if re.search(r'docs/knowledge/(adr|lessons|gotchas)/(ADR|LES|GOT)-\d+', body):
                offenders.append(path.relative_to(ROOT).as_posix())
    assert not offenders, offenders


def test_the_degradation_without_node_is_documented_in_both_languages():
    for rel in ('docs/observability.md', 'docs/en/observability.md'):
        body = text(rel)
        assert 'command not found' in body and 'node' in body and '/doctor' in body, rel
