#!/usr/bin/env python3
"""Read the bundled module catalog with the same contract as the Node installer."""
import argparse
import json
from pathlib import Path
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

CATALOG=Path(__file__).with_name('modules.json')

def _name(value):
    return isinstance(value,str) and len(value)<=100 and re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*',value) is not None

def _names(values,label):
    if not isinstance(values,list) or len(values)>512 or any(not _name(v) for v in values):
        raise ValueError(f'invalid {label}')
    return sorted(set(values))

def load_catalog():
    with CATALOG.open('rb') as handle:
        raw=handle.read(65537)
    if len(raw)>65536:
        raise ValueError('catalog exceeds limit')
    return json.loads(raw)

def validate_catalog(catalog):
    if not isinstance(catalog,dict) or set(catalog)!={'version','modules','profiles'} or type(catalog['version']) is not int or catalog['version']!=1:
        raise ValueError('invalid catalog schema/version')
    modules,profiles=catalog['modules'],catalog['profiles']
    if not isinstance(modules,dict) or not isinstance(profiles,dict) or not 1<=len(modules)<=64 or not 1<=len(profiles)<=32 or any(not _name(v) for v in [*modules,*profiles]):
        raise ValueError('invalid catalog identifiers')
    owned={'skills':set(),'commands':set()}
    for module in modules.values():
        if not isinstance(module,dict) or set(module)!={'skills','commands','requires'}:
            raise ValueError('invalid module fields')
        for field in ('skills','commands','requires'):
            values=_names(module[field],field)
            if len(values)!=len(module[field]):
                raise ValueError(f'duplicate {field}')
            for value in values:
                if field=='requires':
                    if value not in modules: raise ValueError('unknown dependency')
                else:
                    if value in owned[field]: raise ValueError(f'duplicate owner: {value}')
                    owned[field].add(value)
    for values in profiles.values():
        if any(value not in modules for value in _names(values,'profile modules')):
            raise ValueError('unknown profile module')
    done,active=set(),set()
    def visit(key):
        if key in active: raise ValueError('dependency cycle')
        if key in done: return
        active.add(key)
        for dependency in modules[key]['requires']: visit(dependency)
        active.remove(key);done.add(key)
    for key in modules: visit(key)
    return catalog

def resolve_selection(*,profile='core',include=None,exclude=None,catalog=None):
    catalog=validate_catalog(load_catalog() if catalog is None else catalog)
    if not isinstance(profile,str) or profile not in catalog['profiles']:
        raise ValueError('unknown profile')
    added=_names([] if include is None else include,'include')
    removed=_names([] if exclude is None else exclude,'exclude')
    if any(value not in catalog['modules'] for value in added+removed): raise ValueError('unknown module')
    if set(added)&set(removed): raise ValueError('included module is excluded')
    initial=sorted((set(catalog['profiles'][profile])|set(added))-set(removed))
    if not initial: raise ValueError('empty selection')
    selected,reasons=set(),{}
    def add(key,reason):
        if key in removed: raise ValueError(f'excluded dependency: {key}')
        reasons.setdefault(key,set()).add(reason)
        if key in selected: return
        selected.add(key)
        for dependency in sorted(catalog['modules'][key]['requires']): add(dependency,f'required:{key}')
    for key in initial: add(key,'explicit' if key in added else f'profile:{profile}')
    modules=sorted(selected)
    return {'version':1,'profile':profile,'modules':modules,
            'skills':sorted({v for key in modules for v in catalog['modules'][key]['skills']}),
            'commands':sorted({v for key in modules for v in catalog['modules'][key]['commands']}),
            'selected_by':{key:sorted(reasons[key]) for key in modules}}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',default='core')
    parser.add_argument('--with',dest='include',action='append',default=[])
    parser.add_argument('--without',dest='exclude',action='append',default=[])
    args=parser.parse_args(argv)
    try:
        print(json.dumps(resolve_selection(profile=args.profile,include=args.include,exclude=args.exclude),ensure_ascii=True,sort_keys=True))
        return 0
    except (OSError,ValueError,RecursionError):
        print('module selection unavailable: check the bundled catalog and selection',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
