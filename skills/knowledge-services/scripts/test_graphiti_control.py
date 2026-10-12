"""Control markers have isolated context and declared entity exclusions."""
import copy,importlib.util
from pathlib import Path
import pytest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('control_base',HERE/'test_graphiti_transitions.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)

def markers(peer):return [args for name,args in peer.requests if name=='add_memory' and args['name'].endswith(('@superseded','@withdrawn'))]

def test_default_control_markers_exclude_entity_and_disable_previous_context(tmp_path,monkeypatch):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);cfg.pop('transition_relations')
    mod.apply(mod.plan([base.next_version(first)],cfg),cfg)
    marker=markers(peer)[0]
    assert marker.get('previous_episode_uuids')==[]
    assert marker.get('excluded_entity_types')==['Entity']
    assert 'control' in marker.get('custom_extraction_instructions','').lower()
    assert 'no' in marker['custom_extraction_instructions'].lower()

def test_declared_custom_types_are_excluded_for_succession_and_withdrawal_only(tmp_path,monkeypatch):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);cfg.pop('transition_relations')
    cfg['transition_excluded_entity_types']=['Organization','Document','Organization','Entity']
    original=peer.tools_call
    def process(name,args):
        if name=='add_memory' and args['name'].endswith(('@superseded','@withdrawn')):
            if 'Organization' not in args.get('excluded_entity_types',[]):
                peer.requests.append((name,copy.deepcopy(args)));peer.queued.append(copy.deepcopy(args))
                # Model classified an Organization whose description is None: worker fails.
                return peer.output({'message':'Episode queued'})
        return original(name,args)
    peer.tools_call=process
    assert mod.apply(mod.plan([base.next_version(first)],cfg),cfg)['aplicados']==1
    assert mod.apply(mod.plan([],cfg),cfg)['revocados']==1
    assert len(markers(peer))==2
    for marker in markers(peer):
        assert marker['excluded_entity_types']==['Entity','Document','Organization']
        assert marker['previous_episode_uuids']==[]
    data=[args for name,args in peer.requests if name=='add_memory' and not args['name'].endswith(('@superseded','@withdrawn'))]
    assert all('excluded_entity_types' not in args and 'previous_episode_uuids' not in args for args in data)

@pytest.mark.parametrize('value',[None,False,'Organization',[''],['Org\nInjected'],list(map(str,range(129)))])
def test_invalid_control_exclusions_fail_before_any_new_publication(tmp_path,monkeypatch,value):
    mod,peer,cfg,first=base.fixture(tmp_path,monkeypatch);cfg['transition_excluded_entity_types']=value
    before=base.public(tmp_path);requests=len(peer.requests)
    with pytest.raises(mod.ErrorMCP):mod.apply(mod.plan([base.next_version(first)],cfg),cfg)
    assert base.public(tmp_path)==before and not any(name in ('add_memory','add_triplet') for name,args in peer.requests[requests:])
