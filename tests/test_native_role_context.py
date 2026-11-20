"""Context chooses native role IDs from its fixed runtime argument."""
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('shell_helpers', ROOT / 'tests/test_hooks_shell.py')
shell = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shell)
pytestmark = pytest.mark.skipif(shell.BASH is None, reason='Git Bash unavailable')


@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
def test_context_runtime_argument_wins_over_untrusted_claims(tmp_path, runtime):
    project = tmp_path / 'project'
    project.mkdir()
    env = shell.env_de(project, tmp_path)
    env['CUSTOM_AGENTS_RUNTIME'] = 'opencode' if runtime != 'opencode' else 'claude'
    payload = {'hook_event_name': 'SessionStart', 'source': 'compact', 'runtime': env['CUSTOM_AGENTS_RUNTIME']}
    result = subprocess.run([shell.BASH, str(ROOT / 'hooks/session-context.sh'), '--runtime=' + runtime],
                            input=json.dumps(payload), env=env, cwd=project, capture_output=True,
                            text=True, encoding='utf8', errors='replace', timeout=30)
    assert result.returncode == 0, result.stderr
    context = json.loads(result.stdout)['hookSpecificOutput']['additionalContext']
    if runtime == 'claude':
        # plugin-audit-2 T-20: Claude Code gets only the index header (its native listing shows the roles);
        # the runtime argument still wins: Claude's delegation line, never the claimed runtime's.
        assert 'subagent_type' in context and 'custom-agents-' not in context
        assert 'delega con subagent y agent' not in context and 'Skills:' not in context
    else:
        # H-21: the index lists cycle roles first; planner is always visible within the cap (architect may be trimmed).
        assert 'custom-agents-planner' in context
    assert ('spawn_agent' if runtime == 'codex' else 'subagent' if runtime == 'opencode' else 'Agent') in context
