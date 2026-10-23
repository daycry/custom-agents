"""Generation rebuild retains the old publication until exact new readback."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import uuid

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('rebuild_base', HERE / 'test_graphiti_publication.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


class Peer:
    def __init__(self, module, root):
        self.module, self.root = module, root
        self.requests, self.remote, self.queued, self.deferred = [], [], [], []
        self.delay = False
        self.lose_ack = False
        self.publications_during_build = []

    def initialize(self):
        return {}

    def output(self, value):
        return {'isError': False, 'structuredContent': {'result': value}}

    def persist(self, args):
        self.remote.append({'uuid': str(uuid.uuid4()), 'name': args['name'],
                            'group_id': args['group_id'], 'content': args['episode_body'],
                            'source': args['source'], 'source_description': args['source_description']})

    def tools_call(self, name, args):
        self.requests.append((name, copy.deepcopy(args)))
        if name == 'get_episodes':
            rows = [row for row in self.remote if row['group_id'] in args['group_ids']]
            return self.output({'episodes': copy.deepcopy(rows[-args['max_episodes']:])})
        assert name == 'add_memory', 'Rebuild must not clear any published group.'
        assert 'uuid' not in args
        self.queued.append(copy.deepcopy(args))
        if args['group_id'] != 'owned-generation':
            self.publications_during_build.append(public(self.root))
        if self.delay:
            self.deferred.append(copy.deepcopy(args))
        else:
            self.persist(args)
        if self.lose_ack:
            self.lose_ack = False
            raise ConnectionResetError('Owned lost creation response after persistence')
        return self.output({'message': 'Episode queued'})

    def complete(self):
        for args in self.deferred:
            self.persist(args)
        self.deferred.clear()
        self.delay = False


def path(root):
    return root / '.claude/knowledge-services/graphiti-manifest.json'


def public(root):
    return json.loads(path(root).read_bytes()) if path(root).exists() else {}


def fixture(tmp_path, monkeypatch):
    module = base.load()
    peer = Peer(module, tmp_path)
    monkeypatch.setattr(module, 'ClienteMCP', lambda *args, **kwargs: peer)
    cfg = {'_root': str(tmp_path), 'endpoint': 'http://127.0.0.1:8001/mcp',
           'group_id': 'owned-generation', 'mode': 'shadow', 'provider': {'llm': 'none'},
           'timeout_ms': 3000}
    item = base.item()
    module.apply(module.plan([item], cfg), cfg)
    return module, peer, cfg, item


def rebuild_state(root):
    return root / '.claude/knowledge-services/graphiti-rebuild.json'


def mutations(peer, since=0):
    return [(name, args) for name, args in peer.requests[since:] if name != 'get_episodes']


def test_rebuild_switches_only_after_confirmation_and_keeps_prior_group(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    before = public(tmp_path)
    result = module.rebuild([item], cfg)
    after = public(tmp_path)
    assert result['reconstruido'] is True and after['group_id'] != cfg['group_id']
    assert after['logical_group_id'] == cfg['group_id'] and cfg['group_id'] == 'owned-generation'
    assert after['entradas'][item['id']]['uuid'] != before['entradas'][item['id']]['uuid']
    assert any(row['group_id'] == cfg['group_id'] for row in peer.remote)
    assert all(value == before for value in peer.publications_during_build)
    assert module.verify(cfg)['ok'] is True


def test_rebuild_preserves_withdrawn_history_and_remaps_episode_identities(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    second = {**item, 'version': 2, 'cuerpo': 'Project Lyra now uses Borealis.'}
    module.apply(module.plan([second], cfg), cfg)
    module.apply(module.plan([], cfg), cfg)
    before = public(tmp_path)
    module.rebuild([], cfg)
    after = public(tmp_path)
    assert after['entradas'] == {} and set(after['transitions']) == set(before['transitions'])
    rows = {row['name']: row for row in peer.remote if row['group_id'] == after['group_id']}
    assert len(rows) == 4
    for name, meta in after['transitions'].items():
        target = item['id'] + '@' + str(meta['target_version'])
        assert meta['source_episode_uuid'] == rows[target]['uuid']
        assert meta['source_episode_uuid'] != before['transitions'][name]['source_episode_uuid']
        if meta['action'] == 'superseded':
            assert meta['replacement_episode_uuid'] == rows[item['id'] + '@2']['uuid']
        assert meta['retired_episode']['uuid'] == rows[target]['uuid']
    assert module.verify(cfg)['ok'] is True


def test_pending_generation_never_becomes_active_and_retry_does_not_resubmit(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    before = public(tmp_path)
    peer.delay = True
    for _ in range(2):
        with pytest.raises(module.ErrorMCP):
            module.rebuild([item], cfg)
        assert public(tmp_path) == before and module.verify(cfg)['ok'] is True
    assert len(peer.queued) == 2
    peer.complete()
    module.rebuild([item], cfg)
    assert len(peer.queued) == 2 and public(tmp_path)['group_id'] != before['group_id']


def test_lost_stage_ack_is_observed_without_recreating_episode(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    before = public(tmp_path)
    peer.lose_ack = True
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    assert public(tmp_path) == before
    count = len(peer.queued)
    module.rebuild([item], cfg)
    assert len(peer.queued) == count and module.verify(cfg)['ok'] is True


@pytest.mark.parametrize('after_write', [False, True])
def test_publication_cut_recovers_without_another_generation(tmp_path, monkeypatch, after_write):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    original = module._escribir_manifest
    before = public(tmp_path)

    def cut(configuration, value, sufijo=''):
        if configuration['_root'] == cfg['_root'] and not sufijo and value['group_id'] != before['group_id']:
            if after_write:
                original(configuration, value, sufijo)
            raise OSError('Owned final publication cut')
        return original(configuration, value, sufijo)

    with monkeypatch.context() as patch:
        patch.setattr(module, '_escribir_manifest', cut)
        with pytest.raises((module.ErrorMCP, OSError)):
            module.rebuild([item], cfg)
    count = len(peer.queued)
    module.rebuild([item], cfg)
    assert len(peer.queued) == count and module.verify(cfg)['ok'] is True


def test_rebuild_rejects_uncertain_active_submission_before_staging(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    peer.delay = True
    second = {**item, 'version': 2, 'cuerpo': 'Project Lyra uses Borealis.'}
    with pytest.raises(module.ErrorMCP):
        module.apply(module.plan([second], cfg), cfg)
    before, count = public(tmp_path), len(peer.queued)
    with pytest.raises(module.ErrorMCP):
        module.rebuild([second], cfg)
    assert public(tmp_path) == before and len(peer.queued) == count


def test_foreign_untracked_remote_episode_is_not_adopted_or_deleted(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    peer.remote.append({'name': 'foreign@1', 'uuid': 'foreign', 'group_id': cfg['group_id'],
                        'content': 'Untracked external content', 'source': 'text', 'source_description': 'external'})
    before, count = public(tmp_path), len(peer.queued)
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    assert public(tmp_path) == before and len(peer.queued) == count and peer.remote[-1]['uuid'] == 'foreign'


def test_changed_remote_bound_content_blocks_rebuild_before_mutation(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    peer.remote[0]['content'] = 'Changed bound episode'
    before, count = public(tmp_path), len(peer.queued)
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    assert public(tmp_path) == before and len(peer.queued) == count


def test_missing_retired_history_is_not_silently_dropped(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    module.apply(module.plan([], cfg), cfg)
    peer.remote = [row for row in peer.remote if row['name'].endswith('@withdrawn')]
    before, count = public(tmp_path), len(peer.queued)
    with pytest.raises(module.ErrorMCP):
        module.rebuild([], cfg)
    assert public(tmp_path) == before and len(peer.queued) == count


def test_missing_current_episode_can_be_rebuilt_from_exact_canonical_source(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    peer.remote.clear()
    module.rebuild([item], cfg)
    assert module.verify(cfg)['ok'] is True and public(tmp_path)['entradas'][item['id']]['version'] == 1


def test_rebuild_updates_current_corpus_without_losing_version_history(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    second = {**item, 'version': 2, 'cuerpo': 'Project Lyra now uses Borealis.'}
    module.rebuild([second], cfg)
    after = public(tmp_path)
    assert after['entradas'][item['id']]['version'] == 2
    assert item['id'] + '@1@superseded' in after['transitions']
    assert module.verify(cfg)['ok'] is True


def test_removed_canonical_entry_becomes_withdrawn_in_new_generation(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    module.rebuild([], cfg)
    after = public(tmp_path)
    assert after['entradas'] == {} and item['id'] + '@1@withdrawn' in after['transitions']
    assert module.verify(cfg)['ok'] is True


def test_stale_requested_version_cannot_publish_a_partial_corpus(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    second = {**item, 'version': 2, 'cuerpo': 'Project Lyra now uses Borealis.'}
    module.apply(module.plan([second], cfg), cfg)
    before = public(tmp_path)
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    assert public(tmp_path) == before


def test_corrupt_rebuild_descriptor_fails_before_network(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    rebuild_state(tmp_path).write_text('{"schema":1,"schema":1}', encoding='utf8')
    start = len(peer.requests)
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    assert not peer.requests[start:]


def test_changed_endpoint_cannot_adopt_pending_generation(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    peer.delay = True
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    cfg['endpoint'] = 'http://127.0.0.1:8123/mcp'
    start = len(peer.requests)
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    assert not peer.requests[start:]


def test_repeated_completed_request_reuses_the_confirmed_generation(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    module.rebuild([item], cfg)
    before, count = public(tmp_path), len(peer.queued)
    module.rebuild([item], cfg)
    assert public(tmp_path) == before and len(peer.queued) == count


@pytest.mark.parametrize('alter_original', [False, True])
def test_tampered_unsubmitted_snapshot_is_not_published(tmp_path, monkeypatch, alter_original):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    other = {**item, 'id': 'owned.gotcha.zeta', 'cuerpo': 'Project Zeta uses Aurora.'}
    module.apply(module.plan([item, other], cfg), cfg)
    before = public(tmp_path)
    peer.delay = True
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item, other], cfg)
    state = json.loads(rebuild_state(tmp_path).read_bytes())
    row = next(row for row in state['snapshot'] if row['payload']['name'] == other['id'] + '@1')
    row['payload']['episode_body'] = 'Changed unsubmitted documentary content'
    row['body_sha256'] = hashlib.sha256(row['payload']['episode_body'].encode('utf8')).hexdigest()
    if alter_original:
        state['original_manifest']['entradas'][other['id']]['episode_body_sha256'] = row['body_sha256']
    rebuild_state(tmp_path).write_text(json.dumps(state), encoding='utf8')
    peer.complete()
    count = len(peer.queued)
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item, other], cfg)
    assert public(tmp_path) == before and len(peer.queued) == count


def ready_fixture(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    second = {**item, 'version': 2, 'cuerpo': 'Project Lyra now uses Borealis.'}
    module.apply(module.plan([second], cfg), cfg)
    original, before = module._escribir_manifest, public(tmp_path)

    def cut(configuration, value, sufijo=''):
        if configuration['_root'] == cfg['_root'] and not sufijo and value['group_id'] != before['group_id']:
            raise OSError('Owned ready generation publication cut')
        return original(configuration, value, sufijo)

    with monkeypatch.context() as patch:
        patch.setattr(module, '_escribir_manifest', cut)
        with pytest.raises(module.ErrorMCP):
            module.rebuild([second], cfg)
    return module, peer, cfg, second, before


def test_tampered_ready_candidate_cannot_drop_verified_history(tmp_path, monkeypatch):
    module, peer, cfg, item, before = ready_fixture(tmp_path, monkeypatch)
    state = json.loads(rebuild_state(tmp_path).read_bytes())
    state['candidate']['transitions'] = {}
    rebuild_state(tmp_path).write_text(json.dumps(state), encoding='utf8')
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    assert public(tmp_path) == before


def test_seeded_stage_cannot_silently_lose_preexisting_history(tmp_path, monkeypatch):
    module, peer, cfg, item, before = ready_fixture(tmp_path, monkeypatch)
    state = json.loads(rebuild_state(tmp_path).read_bytes())
    state.update(phase='building', candidate=None)
    rebuild_state(tmp_path).write_text(json.dumps(state), encoding='utf8')
    stage_file = tmp_path / '.claude/knowledge-services/graphiti-generations' / state['nonce'] / '.claude/knowledge-services/graphiti-manifest.json'
    stage = json.loads(stage_file.read_bytes())
    stage['transitions'] = {}
    stage_file.write_text(json.dumps(stage), encoding='utf8')
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    assert public(tmp_path) == before


def test_completed_generation_can_be_rebuilt_after_remote_current_loss(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    module.rebuild([item], cfg)
    before = public(tmp_path)
    peer.remote = [row for row in peer.remote if row['group_id'] != before['group_id']]
    module.rebuild([item], cfg)
    assert public(tmp_path)['group_id'] != before['group_id'] and module.verify(cfg)['ok'] is True


def test_completed_generation_recovers_remote_history_from_owned_snapshot(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    second = {**item, 'version': 2, 'cuerpo': 'Project Lyra now uses Borealis.'}
    module.apply(module.plan([second], cfg), cfg)
    module.apply(module.plan([], cfg), cfg)
    module.rebuild([], cfg)
    before = public(tmp_path)
    peer.remote = [row for row in peer.remote if row['group_id'] != before['group_id']]
    module.rebuild([], cfg)
    after = public(tmp_path)
    assert after['group_id'] != before['group_id']
    assert after['entradas'] == {} and set(after['transitions']) == set(before['transitions'])
    assert module.verify(cfg)['ok'] is True


def test_changed_request_retains_uncertain_abandoned_generation(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    before = public(tmp_path)
    peer.delay = True
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    first_state = json.loads(rebuild_state(tmp_path).read_bytes())
    second = {**item, 'version': 2, 'cuerpo': 'Project Lyra now uses Borealis.'}
    with pytest.raises(module.ErrorMCP):
        module.rebuild([second], cfg)
    second_state = json.loads(rebuild_state(tmp_path).read_bytes())
    assert first_state['group_id'] != second_state['group_id'] and public(tmp_path) == before
    archive = tmp_path / '.claude/knowledge-services' / ('graphiti-rebuild.archivado-' + first_state['nonce'] + '.json')
    assert json.loads(archive.read_bytes()) == first_state
    peer.complete()
    module.rebuild([second], cfg)
    assert public(tmp_path)['group_id'] == second_state['group_id']
    assert any(row['group_id'] == first_state['group_id'] for row in peer.remote)
    assert len([args for args in peer.queued if args['group_id'] == first_state['group_id']]) == 1


def test_active_sync_between_rebuild_attempts_cannot_publish_stale_snapshot(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    peer.delay = True
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    abandoned = json.loads(rebuild_state(tmp_path).read_bytes())
    peer.delay = False
    second = {**item, 'version': 2, 'cuerpo': 'Project Lyra now uses Borealis.'}
    module.apply(module.plan([second], cfg), cfg)
    peer.complete()
    module.rebuild([second], cfg)
    assert public(tmp_path)['group_id'] != abandoned['group_id']
    assert public(tmp_path)['entradas'][item['id']]['version'] == 2
    assert module.verify(cfg)['ok'] is True


def test_unowned_stage_directory_cannot_be_reused_for_mutation(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    peer.delay = True
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    state = json.loads(rebuild_state(tmp_path).read_bytes())
    marker = tmp_path / '.claude/knowledge-services/graphiti-generations' / state['nonce'] / '_owner.json'
    marker.unlink()
    start = len(peer.requests)
    with pytest.raises(module.ErrorMCP):
        module.rebuild([item], cfg)
    assert not mutations(peer, start)


def test_rebuild_prunes_each_confirmed_restore_before_receipt_budget_is_exhausted(tmp_path, monkeypatch):
    module, peer, cfg, item = fixture(tmp_path, monkeypatch)
    entries = [item, *[{**item, 'id': 'owned.gotcha.zeta' + str(index),
                       'cuerpo': 'Project Zeta ' + str(index) + ' uses Aurora.'} for index in range(4)]]
    module.apply(module.plan(entries, cfg), cfg)
    monkeypatch.setattr(module._gpub, 'MAX_OPERATIONS', 2)
    module.rebuild(entries, cfg)
    assert len(public(tmp_path)['entradas']) == 5 and module.verify(cfg)['ok'] is True
