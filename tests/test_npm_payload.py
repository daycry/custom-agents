"""Exercise the npm artifact, rather than assuming the Git tree is its payload."""
import json
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_security_tooling_declares_dual_use_content_for_npm_review():
    manifest = json.loads((ROOT / 'package.json').read_bytes())
    assert manifest.get('contentPolicy') == {'class': 'dual-use'}
    assert 'DISCLOSURE' in manifest['files']
    disclosure = (ROOT / 'DISCLOSURE').read_text(encoding='utf8')
    assert 'authorized' in disclosure and 'security' in disclosure


def test_published_payload_contains_dual_use_disclosure(npm_payload):
    package, _ = npm_payload
    assert json.loads((package / 'package.json').read_bytes())['contentPolicy'] == {'class': 'dual-use'}
    assert (package / 'DISCLOSURE').read_bytes() == (ROOT / 'DISCLOSURE').read_bytes()


@pytest.fixture(scope="module")
def npm_payload(tmp_path_factory):
    sandbox = tmp_path_factory.mktemp("npm-payload")
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    assert npm, "npm is required to verify the published payload"
    result = subprocess.run(
        [npm, "pack", "--offline", "--ignore-scripts", "--json",
         "--pack-destination", str(sandbox), "--cache", str(sandbox / "npm-cache")],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    name = json.loads(result.stdout)[0]["filename"]
    unpacked = sandbox / "unpacked"
    unpacked.mkdir()
    with tarfile.open(sandbox / name) as archive:
        members = archive.getmembers()
        assert all(not m.issym() and not m.islnk() for m in members)
        assert all((unpacked / m.name).resolve().is_relative_to(unpacked.resolve()) for m in members)
        archive.extractall(unpacked, members=members, filter="data")
    return unpacked / "package", sandbox


def test_npm_model_projection_has_its_executable_dependency(npm_payload):
    """NPM-01: --models-config must also work outside a Git checkout."""
    package, sandbox = npm_payload
    project = sandbox / "project"
    project.mkdir()
    (project / "models.json").write_text(json.dumps({
        "modelos": {"reviewer": {"model": "ollama/qwen3:32b"}}
    }), encoding="utf-8")
    home = sandbox / "home"
    home.mkdir()
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
               CLAUDE_CONFIG_DIR=str(home / ".claude"), CODEX_HOME=str(home / ".codex"),
               XDG_CONFIG_HOME=str(home / ".config"), CUSTOM_AGENTS_PYTHON=sys.executable)
    node = shutil.which("node")
    assert node, "Node is required to exercise the npm installer"
    script = """
const installer = await import(process.argv[1]);
const providers = await import(process.argv[2]);
const result = installer.cargarModelosNativos(providers.getProvider('opencode'), {
  dir: process.argv[3], scope: 'project', modelsConfig: 'models.json'
});
console.log(JSON.stringify(result.projection.agents));
"""
    result = subprocess.run(
        [node, "--input-type=module", "-e", script,
         (package / "install/install.mjs").as_uri(),
         (package / "install/providers.mjs").as_uri(), str(project)],
        cwd=project, env=env, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=45,
    )
    assert result.returncode == 0, result.stderr
    agents = json.loads(result.stdout)
    assert len(agents) == 1
    assert agents[0]["role"] == "reviewer"
    assert agents[0]["model"] == "ollama/qwen3:32b"
    assert not (project / ".opencode").exists(), "projection must not install or mutate providers"


def test_npm_contains_pdf_editions_linked_from_its_readme(npm_payload):
    """NPM-02: the documented local PDF links must survive npm pack."""
    package, _ = npm_payload
    readme = (package / "README.md").read_text(encoding="utf-8")
    paths = re.findall(r"\]\((output/pdf/[^)#]+\.pdf)\)", readme)
    assert paths, "the package README must expose its PDF manuals"
    missing = []
    for relative in paths:
        pdf = package / relative
        for path in [pdf, pdf.with_suffix(".manifest.json")]:
            if not path.is_file():
                missing.append(path.relative_to(package).as_posix())
    assert not missing, missing
    for relative in paths:
        pdf = package / relative
        edition = json.loads(pdf.with_suffix(".manifest.json").read_text(encoding="utf-8"))
        assert hashlib.sha256(pdf.read_bytes()).hexdigest() == edition["pdf_sha256"]
        for source, digest in edition["sources"].items():
            assert hashlib.sha256((package / source).read_bytes().replace(b"\r\n", b"\n")).hexdigest() == digest


def test_npm_excludes_project_state(npm_payload):
    """Packing must not include local preferences, secrets or knowledge corpus."""
    package, _ = npm_payload
    assert not (package / ".claude").exists()
    assert not (package / ".npmrc").exists()
    assert not (package / "docs/knowledge").exists()
