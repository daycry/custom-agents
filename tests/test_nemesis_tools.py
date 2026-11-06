"""Offline contracts for the optional, pinned Nemesis tool installer."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import shlex
import tarfile
import tempfile
import unittest
import zipfile

TOOLS = Path(__file__).resolve().parents[1] / "agent-kits/nemesis/tools"

def load():
    spec = importlib.util.spec_from_file_location("nemesis_install_tools", TOOLS / "install-tools.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def archive(name="fixture", content=b"verified fixture", link=False):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w:gz") as tar:
        member = tarfile.TarInfo(name)
        member.size = len(content)
        member.mode = 0o755
        if link:
            member.type = tarfile.SYMTYPE
            member.linkname = "../../escape"
            member.size = 0
        tar.addfile(member, None if link else io.BytesIO(content))
    return output.getvalue()

class InstallerPolicy(unittest.TestCase):
    def test_no_mutable_install_sources_or_eval(self):
        shell = (TOOLS / "install-tools.sh").read_text(encoding="utf-8")
        self.assertNotIn("/releases/latest", shell, "runtime release selection is mutable")
        self.assertNotIn("git pull", shell)
        self.assertNotIn("--upgrade", shell)
        self.assertNotIn('eval "$c"', shell)

    def test_shim_preserves_non_path_arguments(self):
        import shlex
        module=load()
        code=r"print('a\\b')"
        argv=["python", "-c", code]
        rendered=module.shim(argv).decode().splitlines()[1]
        self.assertEqual(shlex.split(rendered)[1:-1],argv)

    def test_B2_requirements_checkout_is_explicitly_lf(self):
        repo=TOOLS.parents[2]
        result=subprocess.run(["git","check-attr","eol","--","agent-kits/nemesis/tools/wafw00f-requirements.txt"],cwd=repo,capture_output=True,encoding="utf-8",check=True)
        self.assertTrue(result.stdout.rstrip().endswith(": lf"),result.stdout)

    def test_A01_catalog_describes_current_pinned_installer(self):
        catalog=(TOOLS/"catalog.md").read_text(encoding="utf-8")
        self.assertNotIn("Edita la sección **CATALOG**",catalog)
        self.assertIn("tools-lock.json",catalog)
        self.assertIn("wafw00f-requirements.txt",catalog)

    def test_Claude04_agent_passes_only_explicitly_authorized_tool_names(self):
        agent=(TOOLS.parents[2]/"agents/nemesis.md").read_text(encoding="utf-8")
        command=next(row for row in agent.splitlines() if 'bash "$NEMKIT/tools/install-tools.sh"' in row)
        self.assertIn('--only "<nombres-autorizados-separados-por-coma>"',command)

    def test_reviewed_catalog_and_requirements(self):
        module = load()
        catalog = module.read_catalog()
        self.assertEqual(set(catalog["tools"]), {"nuclei", "httpx", "ffuf", "gitleaks", "trivy", "hadolint", "testssl", "sqlmap", "nikto", "wafw00f"})
        for name, tool in catalog["tools"].items():
            self.assertTrue(tool["version"])
            self.assertTrue(tool["source"].startswith("https://"))
            if tool["kind"] == "source":
                self.assertRegex(tool["revision"], r"^[0-9a-f]{40}$")
                self.assertIn(tool["revision"], tool["url"])
            for asset in tool.get("assets", {"source":tool} if tool["kind"]=="source" else {}).values():
                self.assertRegex(asset["sha256"], r"^[0-9a-f]{64}$")
                self.assertTrue(asset["url"].startswith("https://"))
                self.assertNotIn("latest", asset["url"])
        waf = catalog["tools"]["wafw00f"]
        requirements = (TOOLS / waf["requirements"]).read_bytes()
        self.assertEqual(hashlib.sha256(requirements).hexdigest(), waf["requirements_sha256"])
        rows = [row for row in requirements.decode().splitlines() if row and not row.startswith("#")]
        self.assertEqual(len(rows), len(waf["wheels"]))
        self.assertTrue(all("==" in row and "--hash=sha256:" in row for row in rows))

class OfflineInstaller(unittest.TestCase):
    def setUp(self):
        self.module = load()
        self.temp = tempfile.TemporaryDirectory(prefix="ca-tool-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "tools with apostrophe's"
        self.payload = archive()
        self.calls = []
        self.downloads = []
        self.tool = {"kind":"binary", "version":"v1", "source":"https://github.com/example/tool/releases/tag/v1", "assets":{"linux-amd64":{"url":"https://github.com/example/tool/releases/download/v1/fixture.tgz", "sha256":hashlib.sha256(self.payload).hexdigest(), "format":"tar.gz", "binary":"fixture"}}}
        self.catalog = {"schema_version":1, "tools":{"fixture":self.tool}}
    def installer(self):
        def fetch(url):
            self.downloads.append(url)
            return self.payload
        def run(args, **kwargs):
            self.calls.append((args, kwargs))
            target = Path(args[args.index("--target")+1]) if "--target" in args else None
            if target:
                (target / "wafw00f").mkdir()
                (target / "wafw00f/__init__.py").write_text("# fixture", encoding="utf-8")
        return self.module.Installer(self.root, self.catalog, target="linux-amd64", fetch=fetch, run=run)
    def test_verified_binary_and_idempotent_repeat(self):
        installer = self.installer()
        self.assertEqual(installer.install("fixture"), "installed")
        self.assertEqual((self.root / "bin/fixture").read_bytes(), b"verified fixture")
        self.assertEqual(installer.install("fixture"), "present")
        self.assertEqual(len(self.downloads), 1)
        self.assertEqual(self.calls, [])
    def test_bad_hash_publishes_nothing(self):
        self.tool["assets"]["linux-amd64"]["sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "integrity"):
            self.installer().install("fixture")
        self.assertFalse((self.root / "bin/fixture").exists())
        self.assertEqual(self.calls, [])
    def test_unknown_existing_file_is_preserved_even_with_force(self):
        installer = self.installer()
        installer.prepare()
        path=self.root / "bin/fixture"
        path.write_bytes(b"foreign")
        with self.assertRaisesRegex(ValueError, "unmanaged"):
            installer.install("fixture", force=True)
        self.assertEqual(path.read_bytes(), b"foreign")
        self.assertEqual(self.downloads, [])
    def test_modified_managed_file_is_preserved(self):
        installer=self.installer()
        installer.install("fixture")
        path=self.root / "bin/fixture"
        path.write_bytes(b"locally changed")
        with self.assertRaisesRegex(ValueError, "modified"):
            installer.install("fixture", force=True)
        self.assertEqual(path.read_bytes(), b"locally changed")
    def test_unsafe_archives_and_links_rejected_before_publish(self):
        for name, link in (("../escape",False),("/escape",False),("C:/escape",False),("dir\\escape",False),("fixture",True)):
            with self.subTest(name=name,link=link):
                self.payload=archive(name,link=link)
                self.tool["assets"]["linux-amd64"]["sha256"]=hashlib.sha256(self.payload).hexdigest()
                with self.assertRaises(ValueError):self.installer().install("fixture")
                self.assertFalse((self.root / "bin/fixture").exists())
                self.assertFalse((self.base / "escape").exists())
    def test_ambiguous_binary_rejected(self):
        output=io.BytesIO()
        with zipfile.ZipFile(output,"w") as handle:
            handle.writestr("a/fixture",b"one")
            handle.writestr("b/fixture",b"two")
        self.payload=output.getvalue()
        asset=self.tool["assets"]["linux-amd64"]
        asset.update(format="zip", sha256=hashlib.sha256(self.payload).hexdigest())
        with self.assertRaisesRegex(ValueError,"binary_count"):self.installer().install("fixture")
    def test_missing_platform_has_no_fallback(self):
        self.tool["assets"]={}
        with self.assertRaisesRegex(ValueError,"unsupported_platform"):self.installer().install("fixture")
        self.assertEqual(self.downloads,[])
    def test_project_root_and_symlink_root_rejected(self):
        project=self.base/"project"
        project.mkdir()
        (project/".git").mkdir()
        self.root=project/"tools"
        with self.assertRaisesRegex(ValueError,"project"):self.installer().install("fixture")
        target=self.base/"target"
        target.mkdir()
        self.root=self.base/"linked"
        try:self.root.symlink_to(target,target_is_directory=True)
        except OSError:return
        with self.assertRaises(ValueError):self.installer().install("fixture")
        self.assertEqual(list(target.iterdir()),[])
    def test_source_wrapper_quotes_paths_and_detects_vendor_modification(self):
        self.payload=archive("repo-commit/tool.py",b"print('fixture')")
        self.catalog["tools"]["fixture"]={"kind":"source","version":"v1","revision":"a"*40,"url":"https://codeload.github.com/example/tool/tar.gz/"+"a"*40,"sha256":hashlib.sha256(self.payload).hexdigest(),"entry":"tool.py","runner":"python","source":"https://github.com/example/tool"}
        installer=self.installer()
        installer.install("fixture")
        shim=(self.root/"bin/fixture").read_text(encoding="utf-8")
        self.assertIn("exec ",shim)
        self.assertIn('"$@"',shim)
        self.assertIn("-I -B",shim)
        self.assertNotIn("eval",shim)
        source=next((self.root/"vendor").glob("*/tool.py"))
        source.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"modified"):installer.install("fixture")
        self.assertEqual(self.calls,[])
    def test_B1_source_python_imports_its_verified_sibling_with_isolation(self):
        output=io.BytesIO()
        with tarfile.open(fileobj=output,mode="w:gz") as tar:
            for name,content in (("repo/tool.py",b"import sibling; print(sibling.VALUE)"),("repo/sibling.py",b"VALUE='verified sibling'")):
                member=tarfile.TarInfo(name);member.size=len(content);tar.addfile(member,io.BytesIO(content))
        self.payload=output.getvalue()
        self.catalog["tools"]["fixture"]={"kind":"source","version":"v1","revision":"a"*40,"url":"https://codeload.github.com/example/tool/tar.gz/"+"a"*40,"sha256":hashlib.sha256(self.payload).hexdigest(),"entry":"tool.py","runner":"python","source":"https://github.com/example/tool"}
        self.installer().install("fixture")
        rendered=(self.root/"bin/fixture").read_text(encoding="utf-8").splitlines()[1]
        argv=shlex.split(rendered)[1:-1]
        self.assertIn("-I",argv)
        self.assertIn("-B",argv)
        result=subprocess.run(argv,capture_output=True,encoding="utf-8",env={**os.environ,"PYTHONPATH":str(self.base/"untrusted")},timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(result.stdout.strip(),"verified sibling")

    def test_python_install_is_hash_checked_wheel_only_isolated_and_local(self):
        requirements=b"fixture==1 --hash=sha256:"+b"a"*64+b"\n"
        requirements_path=self.base/"requirements.txt"
        requirements_path.write_bytes(requirements)
        self.catalog["tools"]["fixture"]={"kind":"python","version":"v1","source":"https://pypi.org/project/fixture/1/","requirements":str(requirements_path),"requirements_sha256":hashlib.sha256(requirements).hexdigest()}
        installer=self.installer()
        installer.install("fixture")
        args,kwargs=self.calls[0]
        for token in ("-I","-B","--isolated","--require-hashes","--only-binary=:all:","--no-deps","--target","--no-compile"):self.assertIn(token,args)
        self.assertNotIn("--upgrade",args)
        self.assertEqual(kwargs["env"]["PIP_CONFIG_FILE"],os.devnull)
        self.assertEqual(kwargs["env"].get("PIP_EXTRA_INDEX_URL"),None)
        self.assertTrue(Path(args[args.index("--target")+1]).is_relative_to(self.root))
        self.assertEqual(installer.install("fixture"),"present")

if __name__=="__main__":unittest.main()
