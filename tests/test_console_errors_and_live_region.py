"""Console minors (audit 2026-11-09): user-facing error codes have a message and the chat is a live region."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'skills/plugin-panel/assets'
# Codes the server returns for conditions a person can act on; without an entry the UI shows the generic text.
MISSING_BEFORE_T21 = ('workspace_not_found', 'session_not_found', 'session_not_resumable', 'session_not_running',
                      'runtime_not_enabled', 'native_busy', 'native_connection_lost')


def error_keys():
    source = (ASSETS / 'control-center.js').read_text(encoding='utf-8')
    block = source[source.index('const errors={'):]
    block = block[:block.index('\n\nconst ')]
    return set(re.findall(r"^\s*([a-z_0-9]+):'", block, re.M))


def test_every_actionable_server_code_has_a_message():
    keys = error_keys()
    assert not set(MISSING_BEFORE_T21) - keys, sorted(set(MISSING_BEFORE_T21) - keys)


def test_each_mapped_code_is_one_the_server_can_return_or_a_known_client_code():
    server = ''.join(path.read_text(encoding='utf-8') for path in (ROOT / 'skills/plugin-panel/scripts').glob('*.py'))
    client_only = {'delivery_uncertain', 'native_v2_required', 'service_unavailable'}
    for code in error_keys() - client_only:
        assert f"'{code}'" in server, code


def test_the_chat_is_a_polite_live_region_and_pending_requests_are_announced():
    html = (ASSETS / 'control-center.html').read_text(encoding='utf-8')
    chat = re.search(r'<div id="chat-messages"[^>]*>', html)[0]
    assert 'role="log"' in chat and 'aria-live="polite"' in chat and 'aria-live="off"' not in chat
    requests = re.search(r'<div id="chat-requests"[^>]*>', html)[0]
    assert 'aria-live="polite"' in requests
