"""Preserve commit verification for exact protected roles across native runtimes."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GUARD = load('commit_verification_guard', 'guardrail-check.py')
NATIVE = load('commit_verification_native', 'native-guardrail.py')
ROLES = {'schema_version': 1, 'runtimes': {
    runtime: {role: ('custom-agents:' if runtime == 'claude' else 'custom-agents-') + role
              for role in ('implementer', 'architect', 'planner')}
    for runtime in ('claude', 'codex', 'opencode')}}

DENIED = (
    'git commit --no-verify -m x',
    'git commit -n -m x',
    'git commit -an -m x',
    'git commit --amend --no-verify --no-edit',
    'git commit --amend -n --no-edit',
    'git commit --verify --no-verify -m x',
    'git -c core.hooksPath=/dev/null commit -m x',
    'git -c core.hooksPath= commit --amend --no-edit',
    'git -ccore.hooksPath=/dev/null commit -m x',
    'git -c CORE.HOOKSPATH=alternate commit -m x',
    'git --config-env=core.hooksPath=HOOKS_DIR commit -m x',
    'GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null git commit -m x',
    'env GIT_CONFIG_COUNT=2 GIT_CONFIG_KEY_1=core.hooksPath GIT_CONFIG_VALUE_1=alternate git commit -m x',
    'env X=1 git commit -n -m x',
    'X=1 git commit -n -m x',
    'command git commit -n -m x',
    'exec git commit -n -m x',
    'bash -lc "git commit --no-verify -m x"',
    'env X=1 bash -lc "git commit --no-verify -m x"',
)

ALLOWED = (
    'git commit -m "--no-verify"',
    'git commit -m "core.hooksPath=/dev/null"',
    'git commit --message=--no-verify',
    'git commit -m--no-verify',
    'git commit -am--no-verify',
    'git commit -F --no-verify',
    'git commit --file --no-verify',
    'git commit --amend --no-edit',
    'git commit --no-verify --verify -m x',
    'git commit -- --no-verify',
    'git -c commit.gpgsign=false commit -m x',
    'git -c core.hooksPath=alternate status',
    'GIT_CONFIG_COUNT=0 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=alternate git commit -m x',
    'GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_1=core.hooksPath GIT_CONFIG_VALUE_1=alternate git commit -m x',
    'env X=1 git commit -m x',
    'echo "git commit --no-verify"',
    'bash -lc \'echo "git commit --no-verify"\'',
)

EXTENDED_DENIED = (
    'git commit --no-veri -m x',
    'git commit --no-verif --amend --no-edit',
    'git.exe commit --no-verify -m x',
    'command -p git commit -n -m x',
    'exec -a own-git git commit -n -m x',
    'env -i git commit -n -m x',
    'env --ignore-environment X=1 git commit -n -m x',
    'env -u X git commit -n -m x',
    'env --unset=X git commit -n -m x',
    'GIT_CONFIG_COUNT=+1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=alternate git commit -m x',
    'GIT_CONFIG_COUNT=" 1" GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=alternate git commit -m x',
    'GIT_CONFIG_PARAMETERS="\'core.hooksPath\'=\'alternate\'" git commit -m x',
    'GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=alternate bash -lc "git commit -m x"',
)

EXTENDED_ALLOWED = (
    'git commit --no-veri --veri -m x',
    'git commit --message --no-v',
    'git commit -m--no-v',
    'GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=alternate env -i git commit -m x',
    'GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=alternate env -u GIT_CONFIG_COUNT git commit -m x',
    'GIT_CONFIG_PARAMETERS="\'safe.setting\'=\'core.hooksPath=alternate\'" git commit -m x',
)


def evaluate(command, runtime, role='implementer', tool=None, git=True, identity=None):
    tool = tool or ('shell' if runtime == 'opencode' else 'Bash')
    identity = identity if identity is not None else ROLES['runtimes'][runtime][role]
    key = 'agent' if runtime == 'opencode' else 'agent_type'
    return NATIVE.evaluate({key: identity, 'tool_name': tool,
                            'tool_input': {'command': command}}, runtime, 'owned-fixture',
                           roles=ROLES, cfg={'alcance': True, 'git': git, 'ramaPrincipal': True},
                           branch_fn=lambda _: 'feature/verification')


@pytest.mark.parametrize('runtime,tool', [('claude', 'Bash'), ('claude', 'PowerShell'),
                                         ('codex', 'Bash'), ('opencode', 'shell')])
@pytest.mark.parametrize('role', ['implementer', 'architect'])
@pytest.mark.parametrize('command', DENIED)
def test_native_protected_commit_cannot_skip_verification(runtime, tool, role, command):
    result = evaluate(command, runtime, role, tool)
    assert result['decision'] == 'deny'
    assert result['reason'] and result['diagnostic'] is None


@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
@pytest.mark.parametrize('command', ALLOWED)
def test_native_commit_values_paths_and_normal_amend_are_allowed(runtime, command):
    result = evaluate(command, runtime)
    assert result['decision'] == 'continue' and result['diagnostic'] is None


@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
@pytest.mark.parametrize('role', ['implementer', 'architect'])
def test_project_git_rule_opt_out_preserves_continue(runtime, role):
    assert evaluate(DENIED[0], runtime, role, git=False)['decision'] == 'continue'


@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
@pytest.mark.parametrize('identity', ['consumer-agent', 'implementer', 'architect'])
def test_consumer_or_claimed_name_does_not_activate_commit_guard(runtime, identity):
    result = evaluate(DENIED[0], runtime, identity=identity)
    assert result['decision'] == 'continue' and result['diagnostic'] is None


@pytest.mark.parametrize('wrapper', ['env X=1 ', 'X=1 ', 'command ', 'exec '])
def test_literal_wrappers_cannot_evade_existing_forced_push_guard(wrapper):
    assert GUARD.check_git(wrapper + 'git push --force', 'feature/verification')
    assert GUARD.check_git(wrapper + 'git push', 'feature/verification') is None


@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
@pytest.mark.parametrize('command', EXTENDED_DENIED)
def test_extended_literal_commit_bypass_is_denied(runtime, command):
    assert evaluate(command, runtime)['decision'] == 'deny'


@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
@pytest.mark.parametrize('command', EXTENDED_ALLOWED)
def test_extended_values_and_cleared_environment_are_allowed(runtime, command):
    assert evaluate(command, runtime)['decision'] == 'continue'


@pytest.mark.parametrize('option', ['--mess', '--fil', '--temp', '--trail', '--auth',
                                    '--reuse', '--reed', '--clean', '--pathspec-from-f',
                                    '--reu', '--pathspec-fr', '--c'])
def test_abbreviated_git_value_option_consumes_next_token(option):
    assert GUARD.check_git('git commit ' + option + ' --no-verify', None) is None


@pytest.mark.parametrize('option', ['--no-v', '--no-ver'])
def test_ambiguous_git_verify_abbreviation_is_not_an_effective_flag(option):
    assert GUARD.check_git('git commit ' + option + ' -m x', None) is None


def test_literal_config_counter_with_long_leading_zero_prefix_is_supported():
    assert GUARD.check_git('GIT_CONFIG_COUNT=00000000000001 GIT_CONFIG_KEY_0=core.hooksPath '
                           'GIT_CONFIG_VALUE_0=alternate git commit -m x', None)


def test_noncanonical_config_key_index_is_not_a_git_override():
    assert GUARD.check_git('GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_00=core.hooksPath '
                           'GIT_CONFIG_VALUE_00=alternate git commit -m x', None) is None


@pytest.mark.parametrize('command', [
    'git commit --no-verify --mess --verify',
    'git commit --no-verify --trail --verify -m x',
    'git commit --no-verify --reu --verify -m x',
    'git commit --no-verify --pathspec-fr --verify -m x',
    'exec -c git commit -n -m x', 'exec -l git commit -n -m x',
    'env -uX git commit -n -m x', 'env --chdir=. git commit -n -m x',
    'env -C . git commit -n -m x',
    'GIT.EXE commit -n -m x', 'git.EXE commit -n -m x',
    'Git.exe commit -n -m x', 'GIT commit -n -m x',
])
def test_known_invocation_forms_preserve_effective_commit_denial(command):
    assert GUARD.check_git(command, None)


def test_exec_clear_environment_removes_literal_config_override():
    assert GUARD.check_git('GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath '
                          'GIT_CONFIG_VALUE_0=alternate exec -c git commit -m x', None) is None


def test_env_single_dash_clears_literal_environment_like_ignore_flag():
    assert GUARD.check_git('GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath '
                          'GIT_CONFIG_VALUE_0=alternate env - git commit -m x', None) is None


@pytest.mark.parametrize('restore', ['--no-no-verify', '--no-no-veri'])
def test_git_negated_negative_verify_option_restores_hooks(restore):
    assert GUARD.check_git('git commit --no-verify ' + restore + ' -m x', None) is None


@pytest.mark.parametrize('count', ['2147483648', '9999999999', '\u00a01', '1 ', '-1'])
def test_invalid_git_config_counter_is_not_an_executable_override(count):
    assert GUARD.check_git('GIT_CONFIG_COUNT="' + count + '" GIT_CONFIG_KEY_0=core.hooksPath '
                          'GIT_CONFIG_VALUE_0=alternate git commit -m x', None) is None


@pytest.mark.parametrize('command', [
    'git commit -n -m first\ngit commit --verify -m second',
    'git commit -n # --verify\ngit commit --verify -m second',
    'git commit -m ";" -n', 'git commit -m "&&" -n',
    'git commit -m "\n" -n', 'git commit -m "# --verify" -n',
    'env -C. git commit -n -m x', 'exec -cl git commit -n -m x',
    'env -iu X git commit -n -m x',
    'git commit -n -m x\\\\',
    'git commit -n -m first\necho "unfinished',
])
def test_review_b12_command_boundaries_and_wrapper_clusters_cannot_hide_denial(command):
    assert GUARD.check_git(command, None)


@pytest.mark.parametrize('command', [
    'git commit -n \\\n --verify -m x',
    'git commit -m "first\n--no-verify"',
    'git commit -m "# text" --verify',
    'git commit -m "escaped \\"quote\\""',
    'echo "git commit -n\ngit commit --no-verify"',
])
def test_review_b12_quoted_text_and_line_continuation_preserve_permission(command):
    assert GUARD.check_git(command, None) is None


@pytest.mark.skipif(not shutil.which('node') or not shutil.which('git'), reason='Node/Git unavailable')
@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
@pytest.mark.parametrize('role', ['implementer', 'architect'])
@pytest.mark.parametrize('command,expected', [
    ('git commit --no-verify --mess --verify', 'deny'),
    ('git -c core.hooksPath=alternate commit -m x', 'deny'),
    ('git commit --amend --no-edit', 'continue'),
])
def test_real_launcher_delivers_commit_policy(tmp_path, runtime, role, command, expected):
    root = HERE.parents[1]
    hooks = tmp_path / 'hooks'
    hooks.mkdir()
    shared = tmp_path / 'agent-kits' / 'shared'
    shared.mkdir(parents=True)
    for filename in ('run-hook.mjs', 'runtime-supervisor.py'):
        shutil.copyfile(root / 'hooks' / filename, hooks / filename)
    for filename in ('native-guardrail.py', 'guardrail-check.py', 'native-roles.json'):
        shutil.copyfile(HERE / filename, shared / filename)
    key = 'agent' if runtime == 'opencode' else 'agent_type'
    event = {key: ROLES['runtimes'][runtime][role],
             'tool_name': 'shell' if runtime == 'opencode' else 'Bash',
             'tool_input': {'command': command}}
    # Owned fixture: only branch queries execute; the commit payload never executes.
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'PATHEXT'}}
    env.update(PATH=str(Path(shutil.which('git')).parent), HOME=str(tmp_path), USERPROFILE=str(tmp_path), TEMP=str(tmp_path),
               TMP=str(tmp_path), CUSTOM_AGENTS_PYTHON=sys.executable,
               CLAUDE_PROJECT_DIR=str(tmp_path), PYTHONDONTWRITEBYTECODE='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    subprocess.run([shutil.which('git'), 'init', '-q', '-b', 'feature/verification', str(tmp_path)],
                   env=env, cwd=tmp_path, check=True, capture_output=True, timeout=10)
    result = subprocess.run([shutil.which('node'), str(hooks / 'run-hook.mjs'),
                             'native-guardrail', '--runtime=' + runtime], cwd=tmp_path,
                            env=env, input=json.dumps(event), capture_output=True,
                            encoding='utf-8', timeout=15)
    assert result.returncode == 0, result.stderr
    if expected == 'continue' and runtime != 'opencode':
        assert result.stdout == ''
    else:
        output = json.loads(result.stdout)
        if runtime == 'opencode':
            assert output['decision'] == expected and output['diagnostic'] is None
        else:
            assert output['hookSpecificOutput']['permissionDecision'] == expected
