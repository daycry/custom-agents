#!/usr/bin/env python3
"""Describe project-local integration bindings without executing or authorizing them."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

HERE=Path(__file__).resolve().parent
CONFIG='.claude/integrations.json'
MAX_BYTES=65536
MAX_BINDINGS=64
ID=re.compile(r'[a-z][a-z0-9]*(?:[-.][a-z0-9]+)*\Z')
ADAPTER_ID=re.compile(r'[A-Za-z][A-Za-z0-9_.:-]*\Z')

def _bundled(name):
    path=HERE/(name+'.py')
    if path.is_symlink() or not path.is_file(): raise ValueError('dependency_unavailable')
    previous=sys.dont_write_bytecode
    sys.dont_write_bytecode=True
    try:
        spec=importlib.util.spec_from_file_location('integration_'+name.replace('-','_'),path)
        if spec is None or spec.loader is None: raise ValueError('dependency_unavailable')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode=previous

def _token(value):
    return isinstance(value,str) and len(value)<=100 and ID.fullmatch(value) is not None

def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise ValueError('duplicate_key')
        result[key]=value
    return result

def _constant(_value):
    raise ValueError('invalid_number')

def _json(reader,project,path):
    read=reader.read_text(project,path,max_bytes=MAX_BYTES)
    if read['status']!='ok': return read['status'],None
    try:
        data=json.loads(read['text'],object_pairs_hook=_pairs,parse_constant=_constant)
        pending=[(data,0)];count=0
        while pending:
            value,depth=pending.pop();count+=1
            if depth>16 or count>4096: raise ValueError('structure_limit')
            children=value.values() if isinstance(value,dict) else value if isinstance(value,list) else ()
            pending.extend((child,depth+1) for child in children)
        return 'ok',data
    except (ValueError,RecursionError):
        return 'invalid_json',None

def _list(value):
    if not isinstance(value,list) or len(value)>32 or any(not _token(item) for item in value) or len(set(value))!=len(value):
        raise ValueError('invalid_list')
    return sorted(value)

def _settings(value):
    if not isinstance(value,str) or not value or len(value)>256 or any(ord(c)<32 or 127<=ord(c)<=159 for c in value):
        raise ValueError('invalid_settings_reference')
    normalized=value.replace('\\','/')
    parts=normalized.split('/')
    if len(parts)>32 or any(part in ('','.','..') or ':' in part for part in parts):
        raise ValueError('invalid_settings_reference')
    # This is a lexical reference, not proof of filesystem identity or permission to read it.
    return normalized

def _binding(value):
    allowed={'id','purpose','enabled','contract_version','adapter','events','capabilities','settings'}
    if not isinstance(value,dict) or set(value)-allowed or not _token(value.get('id')):
        raise ValueError('invalid_binding')
    if type(value.get('enabled')) is not bool: raise ValueError('invalid_enabled')
    if not value['enabled']: return None
    if not _token(value.get('purpose')) or type(value.get('contract_version')) is not int or value['contract_version']!=1:
        raise ValueError('unsupported_contract')
    adapter=value.get('adapter')
    if not isinstance(adapter,dict) or set(adapter)!={'kind','name','origin'}:
        raise ValueError('invalid_adapter')
    if adapter['kind'] not in ('skill','tool') or not isinstance(adapter['name'],str) or not 1<=len(adapter['name'])<=128 or ADAPTER_ID.fullmatch(adapter['name']) is None:
        raise ValueError('invalid_adapter')
    origins=('bundle','project','user') if adapter['kind']=='skill' else ('session',)
    if adapter['origin'] not in origins: raise ValueError('invalid_adapter_origin')
    result={'id':value['id'],'purpose':value['purpose'],'contract_version':1,
            'adapter':dict(adapter),'events':_list(value.get('events')),
            'capabilities':_list(value.get('capabilities'))}
    if not result['capabilities']: raise ValueError('missing_capabilities')
    if 'settings' in value: result['settings']=_settings(value['settings'])
    return result

def _result(status,source,bindings=None,diagnostics=None):
    return {'version':1,'status':status,'source':source,'bindings':bindings or [],
            'diagnostics':diagnostics or [],'availability':'unverified',
            'permissions':'unverified','execution':'not_run'}

def _legacy(reader,project):
    entries=[];diagnostics=[];observed=False
    for name in ('jira','confluence'):
        state,data=_json(reader,project,f'.claude/{name}.json')
        if state=='not_found': continue
        observed=True
        if state!='ok' or not isinstance(data,dict) or type(data.get('enabled')) is not bool:
            diagnostics.append({'code':'invalid_legacy_configuration','source':name})
            continue
        if not data['enabled']: continue
        if name=='jira':
            entries.append({'id':'legacy-jira','purpose':'task-tracking','contract_version':1,
                'adapter':{'kind':'skill','name':'jira-sync','origin':'bundle'},
                'events':['plan.created','task.started','task.implemented','task.qa-passed','task.qa-failed','task.done','review.completed','review.gaps','review.worklog'],
                'capabilities':['plan.export','task.progress','task.read','task.comment','worklog.write'],
                'settings':'.claude/jira.json','legacy':True})
        else:
            for action,events in [('publish',['docs.changed','phase.completed']),('pull',[])]:
                entries.append({'id':f'legacy-confluence-{action}','purpose':'documentation','contract_version':1,
                    'adapter':{'kind':'skill','name':f'confluence-{action}','origin':'bundle'},
                    'events':events,'capabilities':[f'docs.{action}'],
                    'settings':'.claude/confluence.json','legacy':True})
    return entries,diagnostics,observed

def route(project,*,event=None,purpose=None,operation=None):
    """Return declarations only. A caller must still verify the actual session and adapter contract."""
    if any(value is not None and not _token(value) for value in (event,purpose,operation)):
        return _result('invalid','input',diagnostics=[{'code':'invalid_filter'}])
    try:
        reader=_bundled('local-read');redactor=_bundled('redact')
        state,data=_json(reader,project,CONFIG)
        if state=='not_found':
            active,diagnostics,observed=_legacy(reader,project);source='legacy'
            if not active and not diagnostics and not observed: return _result('absent','none')
        elif state!='ok':
            status='invalid' if state in ('invalid_json','invalid_encoding','too_large') else 'unavailable'
            return _result(status,CONFIG,diagnostics=[{'code':state}])
        else:
            source=CONFIG
            if not isinstance(data,dict) or set(data)!={'version','bindings'} or type(data['version']) is not int or data['version']!=1 or not isinstance(data['bindings'],list) or len(data['bindings'])>MAX_BINDINGS:
                return _result('invalid',source,diagnostics=[{'code':'invalid_schema'}])
            counts=Counter(item.get('id') for item in data['bindings'] if isinstance(item,dict) and _token(item.get('id')))
            active=[];diagnostics=[]
            for index,item in enumerate(data['bindings']):
                try:
                    if isinstance(item,dict) and _token(item.get('id')) and counts[item['id']]>1:
                        raise ValueError('duplicate_binding_id')
                    record=_binding(item)
                    if record is not None: active.append(record)
                except ValueError as error:
                    diagnostics.append({'code':str(error),'binding_index':index})
        selected=[item for item in active if (event is None or event in item['events'])
                  and (purpose is None or purpose==item['purpose'])
                  and (operation is None or operation in item['capabilities'])]
        selected.sort(key=lambda item:item['id'])
        status=('partial' if selected else 'invalid') if diagnostics else 'declared' if selected else 'no_match' if active else 'disabled'
        result=_result(status,source,selected,diagnostics)
        raw=json.dumps(result,ensure_ascii=True,sort_keys=True)
        if redactor.redactar(raw)!=raw:
            return _result('invalid',source,diagnostics=[{'code':'sensitive_configuration'}])
        return result
    except Exception:  # noqa: BLE001 — optional routing degrades explicitly, without echoing private exception data
        return _result('unavailable',CONFIG,diagnostics=[{'code':'integration_routing_unavailable'}])

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True)
    parser.add_argument('--event')
    parser.add_argument('--purpose')
    parser.add_argument('--operation')
    parser.add_argument('--check',action='store_true',help='return 2 for invalid/unavailable configuration')
    args=parser.parse_args(argv)
    result=route(args.project,event=args.event,purpose=args.purpose,operation=args.operation)
    print(json.dumps(result,ensure_ascii=True,sort_keys=True))
    return 2 if args.check and result['status'] in ('invalid','unavailable','partial') else 0

if __name__=='__main__':
    raise SystemExit(main())
