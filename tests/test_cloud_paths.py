"""Cloud placeholders are local files, while path redirects remain excluded."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULES = (
    ('agent-kits/shared/capability-route.py', '_linked'),
    ('skills/plugin-panel/scripts/build_panel.py', '_unsafe_link'),
    ('skills/outcome-evals/scripts/report_outcomes.py', '_linked'),
)


@pytest.fixture(params=MODULES)
def guard(request):
    path, name = request.param
    spec = importlib.util.spec_from_file_location('cloud_guard', ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, name)


def tagged_path(tag, attributes=0x400, symlink=False):
    return SimpleNamespace(
        lstat=lambda: SimpleNamespace(st_reparse_tag=tag, st_file_attributes=attributes),
        is_symlink=lambda: symlink,
    )


@pytest.mark.parametrize('variant', range(16))
def test_cloud_placeholder_is_not_a_path_redirect(guard, variant):
    assert guard(tagged_path(0x9000001A | (variant << 12))) is False


@pytest.mark.parametrize('tag', [0xA0000003, 0xA000000C, 0x8000001B, 0])
def test_junction_symlink_and_unknown_reparse_are_rejected(guard, tag):
    assert guard(tagged_path(tag)) is True


def test_regular_file_and_posix_symlink(guard):
    assert guard(tagged_path(0, attributes=0)) is False
    assert guard(tagged_path(0, attributes=0, symlink=True)) is True


def test_missing_path_is_not_misclassified_as_link(guard):
    def missing():
        raise FileNotFoundError
    assert guard(SimpleNamespace(lstat=missing)) is False
