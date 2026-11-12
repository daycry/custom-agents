#!/usr/bin/env python3
"""Verify the shipped handbook against its explicit sources and diagram receipts."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

PDF='output/pdf/custom-agents-manual-operativo.pdf'
MANIFEST='output/pdf/custom-agents-manual-operativo.manifest.json'
CHAPTERS=('product','core-workflows','atlassian','redmine','customization','operations','memory','dashboard','knowledge-categories')
REFERENCES=('product','core-workflows','atlassian','redmine','customization','operations')
SOURCES=('docs/CUSTOMIZATION.md',)+tuple('docs/guides/'+name+'.md' for name in CHAPTERS)+tuple(
    'docs/reference/'+name+'.md' for name in REFERENCES)+(
    'docs/examples/integrations/atlassian.json','docs/examples/integrations/project.json',
    'docs/examples/integrations/project-redmine/SKILL.md','docs/examples/integrations/memory.json',
    'docs/examples/memory/taxonomy.json','docs/examples/dashboard/workspaces.json','agent-kits/shared/modules.json',
    'docs/examples/memory/categories/meetings.json','docs/examples/memory/categories/faq.json',
    'docs/examples/memory/categories/mixed.json')
SHA=re.compile('[a-f0-9]{64}')
GUIDES=(('subscription-efficiency','guia-uso-eficiente-claude-codex','Aprovechar la capacidad de Claude y Codex'),
        ('quality-playbook','guia-resultados-calidad-custom-agents','Obtener mejores resultados con custom-agents'))


def editions():
    """Single maintained definition for all three builders and integrity gates."""
    return ({'pdf':PDF,'title':'Manual operativo de custom-agents','sources':SOURCES,'require_workflows':True},)+tuple(
        {'pdf':'output/pdf/'+pdf+'.pdf','title':title,'sources':('docs/guides/'+source+'.md',),'require_workflows':False}
        for source,pdf,title in GUIDES)


def mermaid_blocks(text):
    """Closed top-level Mermaid fences; longer literal code fences are respected.

    Handbook graphs must be unindented top-level fences, not Markdown list or
    blockquote containers. Unsupported graph containers fail before rendering.
    This bounded authoring subset is shared by the builder and stdlib checker;
    renderer receipts still independently reject any Markdown-it disagreement.
    """
    active=None;content=[];blocks=[]
    normalized=text.replace('\r\n','\n').replace('\r','\n')
    for line in re.split(r'(?<=\n)',normalized):
        if active:
            marker,length,info=active
            if re.fullmatch(r' {0,3}'+re.escape(marker)+'{'+str(length)+r',}[ \t]*\n?',line):
                if info=='mermaid':blocks.append(''.join(content).strip()+'\n')
                active=None;content=[]
            elif info=='mermaid':content.append(line)
            continue
        match=re.fullmatch(r'( {0,3})(`{3,}|~{3,})([^\n]*)\n?',line)
        if match:
            indent,marker,info=match.groups();info=info.strip()
            if marker[0]=='`' and '`' in info:continue
            if info=='mermaid' and indent:raise ValueError('unsupported_mermaid_container')
            active=(marker[0],len(marker),info);content=[]
        elif re.match(r'^[ \t]*(?:(?:[-*+]|\d+[.)]|>)[ \t]+)?(?:`{3,}|~{3,})mermaid[ \t]*\n?$',line):
            raise ValueError('unsupported_mermaid_container')
    if active and active[2]=='mermaid':raise ValueError('unclosed_mermaid_fence')
    return blocks

def read(root,name,maximum):
    path=root/name
    resolved=path.resolve(strict=True)
    if not resolved.is_relative_to(root) or path.is_symlink() or not resolved.is_file():raise ValueError('unsafe_source')
    with resolved.open('rb') as handle:data=handle.read(maximum+1)
    if len(data)>maximum:raise ValueError('file_budget')
    return data

def unique(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('duplicate_key')
        result[key]=value
    return result

def _check_edition(root,edition):
    root=Path(root).resolve();issues=[]
    pdf_name=edition['pdf'];names=edition['sources'];manifest_name=pdf_name[:-4]+'.manifest.json'
    try:
        manifest=json.loads(read(root,manifest_name,256*1024),object_pairs_hook=unique)
        if type(manifest) is not dict or manifest.get('schema_version')!=1 or manifest.get('pdf')!=pdf_name or manifest.get('source_hash_method')!='sha256-utf8-lf':
            return ['invalid_manifest']
        sources=manifest.get('sources')
        if type(sources) is not dict:return ['invalid_manifest']
        if set(sources)!=set(names):issues.append('source_set_mismatch')
        pdf=read(root,pdf_name,32*1024*1024)
        if not pdf.startswith(b'%PDF-') or hashlib.sha256(pdf).hexdigest()!=manifest.get('pdf_sha256'):issues.append('pdf_changed')
        expected_diagrams={};workflows=[]
        # Never read paths supplied by the manifest. Only the maintained allowlist.
        for name in names:
            try:
                data=read(root,name,512*1024).replace(b'\r\n',b'\n')
                if hashlib.sha256(data).hexdigest()!=sources.get(name):issues.append('source_changed:'+name)
                text=data.decode('utf-8')
                for index,code in enumerate(mermaid_blocks(text),1):
                    expected_diagrams[(name,index)]=hashlib.sha256(code.encode()).hexdigest()
                if name.startswith('docs/guides/'):
                    workflows.extend(int(n) for n in re.findall(r'^## W-(\d+)[.] ',text,re.M))
            except ValueError as error:
                code=str(error)
                if code not in ('unsupported_mermaid_container','unclosed_mermaid_fence'):code='source_unavailable'
                issues.append(code+':'+name)
            except OSError:issues.append('source_unavailable:'+name)
        actual={};rows=manifest.get('diagrams')
        if type(rows) is not list or len(rows)>128:issues.append('diagram_mismatch')
        else:
            for row in rows:
                if type(row) is not dict or type(row.get('source')) is not str or type(row.get('index')) is not int:
                    issues.append('diagram_mismatch');break
                key=(row['source'],row['index'])
                if key in actual or type(row.get('png_sha256')) is not str or not SHA.fullmatch(row['png_sha256']):
                    issues.append('diagram_mismatch');break
                actual[key]=row.get('sha256')
            if actual!=expected_diagrams:issues.append('diagram_mismatch')
        if (edition['require_workflows'] and not workflows or sorted(workflows)!=list(range(1,len(workflows)+1)) or
                type(manifest.get('workflows')) is not int or manifest['workflows']!=len(workflows)):
            issues.append('workflow_mismatch')
    except (OSError,ValueError,TypeError,RecursionError):return ['handbook_unavailable']
    return list(dict.fromkeys(issues))


def check(root):
    issues=[]
    for edition in editions():
        prefix='' if edition['pdf']==PDF else Path(edition['pdf']).stem+':'
        issues.extend(prefix+issue for issue in _check_edition(root,edition))
    return issues

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args(argv);issues=check(args.root)
    if issues:
        for issue in issues:print('check-handbook: '+issue)
        return 1
    print('check-handbook: PDF, LF-normalized sources, workflows and diagrams match')
    return 0

if __name__=='__main__':raise SystemExit(main())
