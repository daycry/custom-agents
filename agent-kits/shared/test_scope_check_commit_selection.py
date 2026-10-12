"""Public commit-selection regressions with isolated Git fixtures and sibling owner."""
import base64
import copy
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


class TestCommitSelection(unittest.TestCase):
    A = 'src/é área/[A] elegido.txt'
    B = 'src/β previa.txt'
    C = 'src/é área/A elegido.txt'
    NEW = 'src/é área/[N] nuevo.txt'

    def setUp(self):
        executable = shutil.which('git')
        if executable is None:
            self.skipTest('Git executable unavailable')
        self.git_exe = Path(executable).resolve(strict=True)
        self.script = Path(__file__).resolve().with_name('scope-check.py')
        self.tmp = tempfile.TemporaryDirectory(prefix='commit-selection-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        home = self.root / 'closed-home'
        home.mkdir()
        hooks = home / 'empty-hooks'
        hooks.mkdir()
        self.env = {key: os.environ[key] for key in ('SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT')
                    if key in os.environ}
        self.env.update({
            'HOME': str(home), 'USERPROFILE': str(home), 'CODEX_HOME': str(home/'codex'),
            'APPDATA': str(home/'appdata'), 'LOCALAPPDATA': str(home/'localappdata'),
            'TMP': str(home/'tmp'), 'TEMP': str(home/'tmp'), 'TMPDIR': str(home/'tmp'),
            'XDG_CONFIG_HOME': str(home/'xdg/config'), 'XDG_DATA_HOME': str(home/'xdg/data'),
            'XDG_CACHE_HOME': str(home/'xdg/cache'), 'XDG_STATE_HOME': str(home/'xdg/state'),
            'PATH': str(self.git_exe.parent), 'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_SYSTEM': os.devnull,
            'GIT_OPTIONAL_LOCKS': '0', 'GIT_TERMINAL_PROMPT': '0',
            'GIT_AUTHOR_NAME': 'Own fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
            'GIT_COMMITTER_NAME': 'Own fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid',
            'GIT_CONFIG_COUNT': '6',
            'GIT_CONFIG_KEY_0': 'core.fsmonitor', 'GIT_CONFIG_VALUE_0': 'false',
            'GIT_CONFIG_KEY_1': 'core.hooksPath', 'GIT_CONFIG_VALUE_1': str(hooks),
            'GIT_CONFIG_KEY_2': 'core.autocrlf', 'GIT_CONFIG_VALUE_2': 'false',
            'GIT_CONFIG_KEY_3': 'commit.gpgSign', 'GIT_CONFIG_VALUE_3': 'false',
            'GIT_CONFIG_KEY_4': 'core.quotePath', 'GIT_CONFIG_VALUE_4': 'true',
            'GIT_CONFIG_KEY_5': 'core.preloadIndex', 'GIT_CONFIG_VALUE_5': 'false',
            'PYTHONUTF8': '1', 'PYTHONDONTWRITEBYTECODE': '1',
            'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1',
        })
        for key in ('CODEX_HOME','APPDATA','LOCALAPPDATA','TMP','XDG_CONFIG_HOME',
                    'XDG_DATA_HOME','XDG_CACHE_HOME','XDG_STATE_HOME'):
            Path(self.env[key]).mkdir(parents=True, exist_ok=True)
        # Scope's existing git() uses PATH/os.environ; only this closed env is visible.
        original_env = dict(os.environ)
        os.environ.clear(); os.environ.update(self.env)
        self.addCleanup(self.restore_env, original_env)
        template = home / 'empty-template'
        template.mkdir()
        self.git('init', '-q', '-b', 'feature/fila14', '--template=' + str(template))
        for path, data in ((self.A,b'A_BASE\n'), (self.B,b'B_BASE\n'), (self.C,b'C_BASE\n')):
            self.write(path, data)
        self.git('--literal-pathspecs', 'add', '--pathspec-from-file=-',
                 '--pathspec-file-nul', data=self.pathspec(self.A,self.B,self.C))
        self.git('commit', '-qm', 'fixture base')
        self.write(self.A, b'A_TASK_REVIEWED\n')
        self.write(self.B, b'B_FOREIGN_STAGED\n')
        self.git('--literal-pathspecs', 'add', '--pathspec-from-file=-',
                 '--pathspec-file-nul', data=self.pathspec(self.B))
        self.write(self.B, b'B_OTHER_WORKTREE_BYTES\n')
        self.write(self.C, b'C_EXCLUDED_FROM_COMMIT\n')
        self.initial_head = self.git('rev-parse', 'HEAD').strip().decode('ascii')
        self.b_index_entry = self.index_entry(self.B)
        self.b_staged_blob = self.git('show', ':'+self.B)
        spec = importlib.util.spec_from_file_location('scope_commit_selection', self.script)
        self.scope = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.scope)

    @staticmethod
    def restore_env(environment):
        os.environ.clear(); os.environ.update(environment)

    @staticmethod
    def pathspec(*paths):
        return b''.join(path.encode('utf-8')+b'\0' for path in paths)

    def git(self, *args, data=None):
        result = subprocess.run([str(self.git_exe), *args], cwd=self.root,
                                env=self.env, input=data, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr.decode('utf-8',errors='replace'))
        return result.stdout

    def write(self, relative, data):
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def index_entry(self, relative):
        output = self.git('--literal-pathspecs','ls-files','--stage','-z','--',relative)
        entries = [row for row in output.split(b'\0') if row]
        self.assertEqual(len(entries),1)
        return entries[0]

    def observed_state(self):
        return {'head':self.git('rev-parse','HEAD'),
                'index':(self.root/'.git/index').read_bytes(),
                'files':{p:((self.root/p).read_bytes() if (self.root/p).is_file() else None)
                         for p in (self.A,self.B,self.C)},
                'index_lock':(self.root/'.git/index.lock').exists()}

    def preview(self, *paths):
        return self.scope.proyectar_commit(str(self.root), list(paths))

    def validate(self, snapshot):
        return self.scope.validar_seleccion_commit(str(self.root), snapshot)

    def commit_only(self, *paths):
        # Fixture procedural oracle: existing Git builtin, not a new product writer.
        return self.git('--literal-pathspecs','commit','--only',
                        '--pathspec-from-file=-','--pathspec-file-nul',
                        '-m','T-01: reviewed task',data=self.pathspec(*paths))

    def test_fila14_preview_is_readonly_and_separates_chosen_staged_and_excluded(self):
        before = self.observed_state()
        snapshot = self.preview(self.A)
        after = self.observed_state()
        self.assertEqual(before,after)
        self.assertEqual(snapshot['head'],self.initial_head)
        self.assertEqual(snapshot['index_sha256'],hashlib.sha256(before['index']).hexdigest())
        self.assertEqual([row['path'] for row in snapshot['seleccionados']],[self.A])
        self.assertIn(self.B,snapshot['no_seleccionados'])
        self.assertIn(self.C,snapshot['no_seleccionados'])
        staged = {row['path']:row for row in snapshot['staged_ajenos']}
        self.assertEqual(staged[self.B]['blob'],self.b_index_entry.split()[1].decode('ascii'))
        self.assertEqual(snapshot['conflictos'],[])
        expected_patch = self.git('--literal-pathspecs','diff','--no-ext-diff','--no-textconv',
                                  '--binary','HEAD','--',self.A)
        self.assertEqual(snapshot['patch'].encode('utf-8'),expected_patch)
        self.assertEqual(base64.b64decode(snapshot['patch_base64'],validate=True),expected_patch)
        self.assertEqual(snapshot['patch_sha256'],hashlib.sha256(expected_patch).hexdigest())
        self.assertIn('A_TASK_REVIEWED',snapshot['patch'])
        self.assertNotIn('B_FOREIGN_STAGED',snapshot['patch'])
        self.assertNotIn('C_EXCLUDED_FROM_COMMIT',snapshot['patch'])

    def test_fila14_builtin_only_commits_reviewed_A_and_preserves_exact_B_staging(self):
        snapshot = self.preview(self.A)
        self.assertTrue(self.validate(snapshot)['valido'])
        reviewed_blob = snapshot['seleccionados'][0]['blob_commit']
        self.commit_only(self.A)
        self.assertNotEqual(self.git('rev-parse','HEAD').strip().decode('ascii'),self.initial_head)
        self.assertEqual(self.git('diff-tree','--no-commit-id','--name-only','-r','-z','HEAD'),
                         self.pathspec(self.A))
        self.assertEqual(self.git('show','HEAD:'+self.A),b'A_TASK_REVIEWED\n')
        self.assertEqual(self.git('rev-parse','HEAD:'+self.A).strip().decode('ascii'),reviewed_blob)
        self.assertEqual(self.git('show','HEAD:'+self.B),b'B_BASE\n')
        self.assertEqual(self.index_entry(self.B),self.b_index_entry)
        self.assertEqual(self.git('show',':'+self.B),self.b_staged_blob)
        self.assertEqual((self.root/self.B).read_bytes(),b'B_OTHER_WORKTREE_BYTES\n')
        self.assertEqual(self.git('show','HEAD:'+self.C),b'C_BASE\n')
        self.assertEqual((self.root/self.C).read_bytes(),b'C_EXCLUDED_FROM_COMMIT\n')
        self.assertEqual(self.git('--literal-pathspecs','diff','--cached','--name-only','-z','--',self.A),b'')
        self.assertEqual(self.git('show',':'+self.A),self.git('show','HEAD:'+self.A))

    def test_fila14_A_change_after_preview_invalidates_without_writes(self):
        snapshot = self.preview(self.A)
        self.write(self.A,b'A_CHANGED_AFTER_PREVIEW\n')
        before = self.observed_state()
        result = self.validate(snapshot)
        self.assertFalse(result['valido'])
        self.assertTrue(any(row['code']=='selected_changed' and row['path']==self.A
                            for row in result['motivos']))
        self.assertEqual(self.observed_state(),before)

    def test_fila14_foreign_staging_in_A_is_conflict_and_not_silently_replaced(self):
        self.write(self.A,b'A_FOREIGN_STAGED\n')
        self.git('--literal-pathspecs','add','--pathspec-from-file=-',
                 '--pathspec-file-nul',data=self.pathspec(self.A))
        foreign_entry = self.index_entry(self.A)
        self.write(self.A,b'A_TASK_WITH_FOREIGN_STAGING\n')
        before = self.observed_state()
        snapshot = self.preview(self.A)
        self.assertTrue(any(row['path']==self.A and row['code']=='staged_conflict'
                            for row in snapshot['conflictos']))
        self.assertFalse(self.validate(snapshot)['valido'])
        self.assertEqual(self.observed_state(),before)
        self.assertEqual(self.index_entry(self.A),foreign_entry)
        self.assertEqual(self.git('show',':'+self.A),b'A_FOREIGN_STAGED\n')

    def test_fila14_new_selected_file_requires_explicit_intent_to_add_then_preserves_B(self):
        self.write(self.NEW,b'NEW_TASK_REVIEWED\n')
        index_unregistered = (self.root/'.git/index').read_bytes()
        unregistered = self.preview(self.NEW)
        self.assertTrue(any(row['path']==self.NEW and row['code']=='new_unregistered'
                            for row in unregistered['conflictos']))
        self.assertFalse(self.validate(unregistered)['valido'])
        self.assertEqual((self.root/'.git/index').read_bytes(),index_unregistered)
        # Caller explicitly registers exactly NEW; reader cannot stage anything.
        self.git('--literal-pathspecs','add','--intent-to-add','--pathspec-from-file=-',
                 '--pathspec-file-nul',data=self.pathspec(self.NEW))
        index_before = (self.root/'.git/index').read_bytes()
        snapshot = self.preview(self.NEW)
        self.assertEqual(snapshot['seleccionados'][0]['estado'],'nuevo')
        self.assertEqual(snapshot['conflictos'],[])
        self.assertEqual((self.root/'.git/index').read_bytes(),index_before)
        self.assertTrue(self.validate(snapshot)['valido'])
        self.commit_only(self.NEW)
        self.assertEqual(self.git('diff-tree','--no-commit-id','--name-only','-r','-z','HEAD'),
                         self.pathspec(self.NEW))
        self.assertEqual(self.git('show','HEAD:'+self.NEW),b'NEW_TASK_REVIEWED\n')
        self.assertEqual(self.index_entry(self.B),self.b_index_entry)
        self.assertEqual(self.git('show',':'+self.B),self.b_staged_blob)
        self.assertEqual(self.git('--literal-pathspecs','diff','--cached','--name-only','-z','--',self.NEW),b'')

    def test_fila14_index_change_after_preview_invalidates_even_if_A_is_unchanged(self):
        snapshot = self.preview(self.A)
        self.write(self.B,b'B_NEW_FOREIGN_STAGING\n')
        self.git('--literal-pathspecs','add','--pathspec-from-file=-',
                 '--pathspec-file-nul',data=self.pathspec(self.B))
        before = self.observed_state()
        result = self.validate(snapshot)
        self.assertFalse(result['valido'])
        self.assertIn('index_changed',[row['code'] for row in result['motivos']])
        self.assertEqual(self.observed_state(),before)

    def test_fila14_HEAD_change_after_preview_invalidates_even_if_A_is_unchanged(self):
        snapshot = self.preview(self.A)
        self.git('commit','--only','--allow-empty','-m','fixture concurrent HEAD advance')
        before = self.observed_state()
        self.assertNotEqual(before['head'].strip().decode('ascii'),snapshot['head'])
        result = self.validate(snapshot)
        self.assertFalse(result['valido'])
        self.assertIn('head_changed',[row['code'] for row in result['motivos']])
        self.assertEqual(self.observed_state(),before)

    def test_fila14_non_UTF8_plaintext_patch_keeps_exact_bytes_as_base64_and_SHA(self):
        self.write(self.A,b'A_PLAIN_\xff_REVIEWED\n')  # No NUL: Git treats it as text.
        before = self.observed_state()
        snapshot = self.preview(self.A)
        raw_patch = self.git('--literal-pathspecs','diff','--no-ext-diff','--no-textconv',
                             '--binary','HEAD','--',self.A)
        self.assertIn(b'\xff',raw_patch)
        self.assertEqual(base64.b64decode(snapshot['patch_base64'],validate=True),raw_patch)
        self.assertEqual(snapshot['patch_sha256'],hashlib.sha256(raw_patch).hexdigest())
        self.assertIsInstance(snapshot['patch'],str)  # Display projection only.
        self.assertFalse(snapshot['patch_display_lossless'])
        self.assertEqual(snapshot['seleccionados'][0]['worktree_sha256'],
                         hashlib.sha256((self.root/self.A).read_bytes()).hexdigest())
        self.assertEqual(self.observed_state(),before)

    def test_fila14_invalid_selections_are_rejected_without_repo_effects(self):
        invalid = ([], [self.A,self.A], ['../outside.txt'], [str(self.root/self.A)],
                   ['src'], ['src/'], [':(glob)src/**'], ['src/x\0.txt'], [None])
        for paths in invalid:
            with self.subTest(paths=paths):
                before = self.observed_state()
                with self.assertRaises(ValueError): self.preview(*paths)
                self.assertEqual(self.observed_state(),before)

    def test_fila14_selected_deletion_is_reviewed_and_only_commit_preserves_B(self):
        (self.root/self.A).unlink()
        before = self.observed_state()
        snapshot = self.preview(self.A)
        entry = snapshot['seleccionados'][0]
        self.assertEqual(entry['path'],self.A)
        self.assertEqual(entry['estado'],'eliminado')
        self.assertIsNone(entry['blob_commit'])
        self.assertIsNone(entry['worktree_sha256'])
        self.assertEqual(snapshot['conflictos'],[])
        raw_patch = self.git('--literal-pathspecs','diff','--no-ext-diff','--no-textconv',
                             '--binary','HEAD','--',self.A)
        self.assertEqual(base64.b64decode(snapshot['patch_base64'],validate=True),raw_patch)
        self.assertEqual(self.observed_state(),before)
        self.assertTrue(self.validate(snapshot)['valido'])
        self.commit_only(self.A)
        self.assertEqual(self.git('diff-tree','--no-commit-id','--name-only','-r','-z','HEAD'),
                         self.pathspec(self.A))
        self.assertEqual(self.git('--literal-pathspecs','ls-tree','-z','HEAD','--',self.A),b'')
        self.assertEqual(self.git('--literal-pathspecs','ls-files','-z','--',self.A),b'')
        self.assertEqual(self.index_entry(self.B),self.b_index_entry)
        self.assertEqual(self.git('show',':'+self.B),self.b_staged_blob)
        self.assertEqual((self.root/self.B).read_bytes(),b'B_OTHER_WORKTREE_BYTES\n')
        self.assertEqual((self.root/self.C).read_bytes(),b'C_EXCLUDED_FROM_COMMIT\n')

    def test_fila14_mode_only_foreign_staging_is_conflict_even_when_blob_is_same(self):
        original = self.index_entry(self.A).split()
        snapshot_before = self.preview(self.A)
        # Actual Git-index mode transition, portable to Windows; no fake chmod claim.
        # --chmod also refreshes the worktree blob. cacheinfo is an actual
        # index-only mode transition of the SAME observed OID, not a fake chmod.
        self.git('update-index','--cacheinfo',
                 '100755,'+original[1].decode('ascii')+','+self.A)
        changed = self.index_entry(self.A).split()
        self.assertEqual(changed[0],b'100755')
        self.assertNotEqual(changed[0],original[0])
        self.assertEqual(changed[1],original[1])
        before = self.observed_state()
        snapshot = self.preview(self.A)
        self.assertTrue(any(row['path']==self.A and row['code']=='staged_conflict'
                            for row in snapshot['conflictos']))
        entry = snapshot['seleccionados'][0]
        self.assertEqual(entry['head_mode'],'100644')
        self.assertEqual(entry['index_mode'],'100755')
        self.assertFalse(self.validate(snapshot)['valido'])
        self.assertIn('index_changed',[row['code'] for row in self.validate(snapshot_before)['motivos']])
        self.assertEqual(self.observed_state(),before)

    def test_fila14_malformed_and_altered_snapshots_are_rejected_readonly(self):
        snapshot = self.preview(self.A)
        malformed = (None, [], {}, {'schema_version':2}, {'schema_version':1})
        tampered = []
        for field,value in (('head','0'*40), ('patch_base64',base64.b64encode(b'fake patch').decode('ascii')),
                            ('patch_base64','@@@not-base64@@@'), ('patch','fake display'),
                            ('patch_display_lossless',not snapshot['patch_display_lossless']),
                            ('patch_sha256','0'*64), ('snapshot_id','0'*64)):
            item = copy.deepcopy(snapshot); item[field]=value; tampered.append(item)
        item = copy.deepcopy(snapshot); item['seleccionados'][0]['path']=self.C; tampered.append(item)
        item = copy.deepcopy(snapshot); item['seleccionados'][0]['blob_commit']='0'*40; tampered.append(item)
        # Integrity is not authentication: malformed shapes must be rejected
        # even if a caller recomputes the documented canonical digest.
        for field,value in (('seleccionados',[{'path':self.A}]),
                            ('conflictos',[{'code':7}]),
                            ('no_seleccionados',{}), ('head',None)):
            item = copy.deepcopy(snapshot); item[field]=value
            body = {key:value for key,value in item.items() if key!='snapshot_id'}
            item['snapshot_id']=hashlib.sha256(json.dumps(
                body,sort_keys=True,ensure_ascii=True,separators=(',',':'),
                allow_nan=False).encode('utf-8')).hexdigest()
            tampered.append(item)
        for item in (*malformed,*tampered):
            with self.subTest(snapshot=item):
                before = self.observed_state()
                result = self.validate(item)
                self.assertFalse(result['valido'])
                self.assertIn('invalid_snapshot',[row['code'] for row in result['motivos']])
                self.assertEqual(self.observed_state(),before)

    def transformer_command(self, name):
        # Owned canary only. No process is started while preparing these tests.
        script = self.root/'closed-home'/(name+'.py')
        script.write_text("from pathlib import Path\n"
                          "Path(__file__).with_suffix('.ran').write_bytes(b'EXECUTED')\n"
                          "print('TRANSFORMED_CUSTOM_CONTENT')\n",encoding='utf-8')
        command = '"'+sys.executable+'" -I -X utf8 -B "'+str(script)+'"'
        return command,script.with_suffix('.ran')

    def test_fila14_external_diff_and_textconv_are_not_executed_by_reader(self):
        command, marker = self.transformer_command('diff-canary')
        self.write('.gitattributes',b'*.txt diff=own-canary\n')
        self.git('config','diff.external',command)
        self.git('config','diff.own-canary.textconv',command)
        before = self.observed_state()
        snapshot = self.preview(self.A)
        self.assertFalse(marker.exists())
        raw_patch = self.git('--literal-pathspecs','diff','--no-ext-diff','--no-textconv',
                             '--binary','HEAD','--',self.A)
        self.assertEqual(base64.b64decode(snapshot['patch_base64'],validate=True),raw_patch)
        self.assertTrue(self.validate(snapshot)['valido'])
        self.assertFalse(marker.exists())
        self.assertEqual(self.observed_state(),before)

    def test_fila14_custom_clean_filter_is_reported_before_projecting_a_commit_blob(self):
        command, marker = self.transformer_command('clean-canary')
        self.write('.gitattributes',b'*.txt filter=own-canary\n')
        self.git('config','filter.own-canary.clean',command)
        self.git('config','filter.own-canary.required','true')
        before = self.observed_state()
        snapshot = self.preview(self.A)
        self.assertTrue(any(row['path']==self.A and row['code']=='custom_filter_unsupported'
                            for row in snapshot['conflictos']))
        self.assertIsNone(snapshot['seleccionados'][0]['blob_commit'])
        self.assertFalse(self.validate(snapshot)['valido'])
        self.assertFalse(marker.exists())
        self.assertEqual(self.observed_state(),before)

    def test_fila14_unselected_custom_filter_is_not_executed_to_list_other_changes(self):
        command, marker = self.transformer_command('unselected-clean-canary')
        self.write('.gitattributes',('"'+self.B+'" filter=own-canary\n').encode('utf-8'))
        self.git('config','filter.own-canary.clean',command)
        self.git('config','filter.own-canary.required','true')
        before = self.observed_state()
        snapshot = self.preview(self.A)
        self.assertFalse(marker.exists())
        self.assertTrue(any(row['code']=='custom_filter_unsupported' and row['path']==self.B
                            for row in snapshot['limites']))
        # Reader may report a partial projection; never claim unsupported scan exact.
        self.assertEqual(self.observed_state(),before)

    def test_fila14_reader_pins_optional_locks_itself_when_caller_omits_them(self):
        before = self.observed_state()
        saved = os.environ.pop('GIT_OPTIONAL_LOCKS',None)
        original_run = self.scope.subprocess.run
        observed = []
        def checked_run(argv,*args,**kwargs):
            if Path(argv[0]).name.lower() in ('git','git.exe'):
                observed.append(kwargs.get('env'))
                self.assertEqual((kwargs.get('env') or {}).get('GIT_OPTIONAL_LOCKS'),'0')
            return original_run(argv,*args,**kwargs)
        self.scope.subprocess.run = checked_run
        try:
            snapshot = self.preview(self.A)
            self.assertTrue(self.validate(snapshot)['valido'])
            self.assertTrue(observed)
            self.assertNotIn('GIT_OPTIONAL_LOCKS',os.environ)
        finally:
            self.scope.subprocess.run = original_run
            if saved is not None: os.environ['GIT_OPTIONAL_LOCKS']=saved
        self.assertEqual(self.observed_state(),before)

    def test_fila14_unselected_huge_bodies_are_not_read_by_Python(self):
        # A real sparse large tracked C, not a mocked byte count. Its content is
        # outside the chosen scope; native Git may determine changed names.
        with (self.root/self.C).open('wb') as handle:
            handle.truncate(64*1024*1024)
        original = Path.read_bytes
        forbidden = {(self.root/self.B).resolve(),(self.root/self.C).resolve()}
        def canary(path):
            if path.resolve() in forbidden:
                self.fail('Python read an unselected body: '+str(path))
            return original(path)
        with patch.object(Path,'read_bytes',canary):
            snapshot = self.preview(self.A)
            self.assertTrue(self.validate(snapshot)['valido'])
        self.assertIn(self.B,snapshot['no_seleccionados'])
        self.assertIn(self.C,snapshot['no_seleccionados'])

    def test_fila14_descriptor_metadata_matches_safe_reader(self):
        local=self.scope._commit_reader()
        data=local.read_bytes(self.root,self.A,max_bytes=8*1024*1024,
                              include_digest=True,include_identity=True)
        after,_=local._checked(self.root,self.root/self.A)
        self.assertEqual(data['status'],'ok')
        self.assertEqual(local._identity(after),data['identity'])
        self.assertEqual(local._generation(after)[:2],data['generation'][:2])

    def test_fila14_replaced_selected_directory_returns_explicit_invalid(self):
        snapshot = self.preview(self.A)
        (self.root/self.A).unlink(); (self.root/self.A).mkdir()
        before = self.observed_state()
        result = self.validate(snapshot)
        self.assertFalse(result['valido'])
        self.assertIn('selected_unavailable',[row['code'] for row in result['motivos']])
        self.assertEqual(self.observed_state(),before)

    def test_fila14_missing_index_returns_explicit_invalid_without_recreating_it(self):
        snapshot = self.preview(self.A)
        (self.root/'.git/index').unlink()
        result = self.validate(snapshot)
        self.assertFalse(result['valido'])
        self.assertIn('projection_unavailable',[row['code'] for row in result['motivos']])
        self.assertFalse((self.root/'.git/index').exists())
        self.assertFalse((self.root/'.git/index.lock').exists())

    def test_fila14_rehashed_snapshot_cannot_hide_other_staged_paths(self):
        snapshot = self.preview(self.A)
        snapshot['staged_ajenos']=[]; snapshot['no_seleccionados']=[]; snapshot['limites']=[]
        body={key:value for key,value in snapshot.items() if key!='snapshot_id'}
        snapshot['snapshot_id']=hashlib.sha256(json.dumps(body,sort_keys=True,
            ensure_ascii=True,separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()
        before=self.observed_state()
        result=self.validate(snapshot)
        self.assertFalse(result['valido'])
        self.assertIn('view_changed',[row['code'] for row in result['motivos']])
        self.assertEqual(self.observed_state(),before)

    def test_fila14_selected_hardlink_and_oversize_are_explicit_conflicts(self):
        alias=self.root/'closed-home/linked-A.txt'
        os.link(self.root/self.A,alias)
        linked=self.preview(self.A)
        self.assertIn('selected_hardlink',[row['code'] for row in linked['conflictos']])
        self.assertIsNone(linked['seleccionados'][0]['blob_commit'])
        self.assertFalse(self.validate(linked)['valido'])
        alias.unlink()
        with (self.root/self.A).open('wb') as handle: handle.truncate(8*1024*1024+1)
        large=self.preview(self.A)
        self.assertIn('selected_too_large',[row['code'] for row in large['conflictos']])
        self.assertIsNone(large['seleccionados'][0]['blob_commit'])
        self.assertFalse(self.validate(large)['valido'])

    def test_fila14_unselected_parent_redirect_is_metadata_only(self):
        other='foreign/holder/private.txt'
        self.write(other,b'OWN_PRIVATE_SENTINEL\n')
        self.git('--literal-pathspecs','add','--pathspec-from-file=-',
                 '--pathspec-file-nul',data=self.pathspec(other))
        self.commit_only(other)
        holder=self.root/'foreign/holder'
        destination=self.root/'closed-home/redirect-target'
        holder.rename(destination)
        try:
            os.symlink(destination,holder,target_is_directory=True)
        except OSError as exc:
            self.skipTest('OWN directory symlink unavailable: '+str(getattr(exc, 'winerror', exc.errno)))
        self.addCleanup(holder.unlink)
        original=Path.read_bytes
        def canary(path):
            if path == self.root/other: self.fail('unselected redirected body read')
            return original(path)
        with patch.object(Path,'read_bytes',canary):
            snapshot=self.preview(self.A)
            self.assertTrue(self.validate(snapshot)['valido'])
        self.assertIn({'path':other,'code':'unselected_unavailable'},snapshot['limites'])

    @unittest.skipUnless(hasattr(os,'mkfifo'),'native FIFO unavailable on this Windows host')
    def test_fila14_unselected_FIFO_is_metadata_only(self):
        (self.root/self.C).unlink()
        os.mkfifo(self.root/self.C)
        self.addCleanup((self.root/self.C).unlink)
        snapshot=self.preview(self.A)
        self.assertTrue(self.validate(snapshot)['valido'])
        self.assertIn({'path':self.C,'code':'unselected_unavailable'},snapshot['limites'])


if __name__=='__main__':
    unittest.main()
