"""Real outbox replay must be reconciled with the current canonical approved corpus."""
import importlib.util
import json
from pathlib import Path
import pytest

HERE=Path(__file__).resolve().parent
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

@pytest.mark.parametrize('current',['withdrawn','unchanged'])
def test_replayed_publication_is_replanned_from_current_approved(tmp_path,capsys,current):
    sync=load(HERE/'knowledge-sync.py','replay_order_sync')
    backend=load(HERE.parent/'backends/markdown_export.py','replay_order_backend')
    outbox=load(HERE.parents[2]/'agent-kits/shared/outbox.py','replay_order_outbox')
    root=tmp_path/'project';cfgdir=root/'.claude/knowledge-services';cfgdir.mkdir(parents=True)
    projection=tmp_path/'projection';cfg={'export_dir':str(projection),'_root':str(root)}
    taxonomy={'version':1,'id_prefix':'ks','categories':[{'key':'GOTCHA','folder':'gotchas','min_evidence':'validated_case','routing':{'docs':True}}],
              'backends':{'docs':{'type':'markdown-export','enabled':True,'config':{'export_dir':str(projection)}}}}
    (cfgdir/'taxonomy.json').write_text(json.dumps(taxonomy),encoding='utf8')
    approved=root/'docs/knowledge/approved/gotchas/queued.md';approved.parent.mkdir(parents=True)
    original='---\nid: ks.gotcha.queued\nversion: 1\nestado: aprobado\ncategory: GOTCHA\nevidencia: validated_case\nfuentes: [docs/evidence.md]\ntags: [area:testing]\n---\n\n# Canonical version\nOriginal approved body.\n'
    approved.write_text(original,encoding='utf8')
    argv=['--root',str(root),'--backend','docs','--json']
    assert sync.main(argv+['--dry-run'])==0
    first=json.loads(capsys.readouterr().out);assert len(first['ops'])==1 and first['ops'][0]['accion']=='upsert'
    if current=='unchanged':
        backend.apply(first['ops'],cfg)
        original_projection=(projection/'ks.gotcha.queued.md').read_bytes()
        approved.write_text(original.replace('version: 1','version: 2').replace('Original approved body.','Superseded queued body.'),encoding='utf8')
        assert sync.main(argv+['--dry-run'])==0
        queued=json.loads(capsys.readouterr().out)['ops']
        approved.write_text(original,encoding='utf8')
    else:
        backend.apply([],cfg);queued=first['ops'];approved.unlink()
    neighbor=projection/'unowned.txt';neighbor.write_bytes(b'Keep unrelated projection bytes.\n')
    queue=cfgdir/'_sync-outbox/docs'
    assert outbox.escribir(str(queue),'earlier-pending',{'backend':'docs','type':'markdown-export','ops':queued})
    assert sync.main(argv)==0
    capsys.readouterr()
    published=projection/'ks.gotcha.queued.md'
    if current=='withdrawn':
        assert not published.exists(),'Replay reintroduced a withdrawn entry after the fresh plan was calculated.'
        assert json.loads((projection/'manifest.json').read_bytes())['entries']=={}
    else:
        assert published.read_bytes()==original_projection,'Replay replaced the unchanged canonical projection with superseded queued content.'
    assert neighbor.read_bytes()==b'Keep unrelated projection bytes.\n'
    assert not (projection/'manifest.pending.json').exists()
    assert outbox.estado(str(queue))['outbox']==0


def test_partial_publication_reports_pending_recovery_and_can_resume(tmp_path,capsys,monkeypatch):
    sync=load(HERE/'knowledge-sync.py','partial_publication_sync')
    backend=load(HERE.parent/'backends/markdown_export.py','partial_publication_backend')
    outbox=load(HERE.parents[2]/'agent-kits/shared/outbox.py','partial_publication_outbox')
    root=tmp_path/'project';cfgdir=root/'.claude/knowledge-services';cfgdir.mkdir(parents=True)
    projection=tmp_path/'projection'
    taxonomy={'version':1,'id_prefix':'ks','categories':[{'key':'GOTCHA','folder':'gotchas','min_evidence':'validated_case','routing':{'docs':True}}],
              'backends':{'docs':{'type':'markdown-export','enabled':True,'config':{'export_dir':str(projection)}}}}
    (cfgdir/'taxonomy.json').write_text(json.dumps(taxonomy),encoding='utf8')
    approved=root/'docs/knowledge/approved/gotchas';approved.mkdir(parents=True)
    sources={}
    for name in ('first','second'):
        path=approved/(name+'.md')
        text=f'---\nid: ks.gotcha.{name}\nversion: 1\nestado: aprobado\ncategory: GOTCHA\nevidencia: validated_case\nfuentes: [docs/evidence.md]\ntags: [area:testing]\n---\n\nOriginal {name} body.\n'
        path.write_text(text,encoding='utf8');sources[path]=text
    argv=['--root',str(root),'--backend','docs','--json']
    assert sync.main(argv)==0;capsys.readouterr()
    old_manifest=(projection/'manifest.json').read_bytes()
    old_bytes={p:p.read_bytes() for p in projection.glob('*.md')}
    neighbor=projection/'unowned.txt';neighbor.write_bytes(b'Unrelated bytes.\n')
    for path,text in sources.items():path.write_text(text.replace('version: 1','version: 2').replace('Original','Updated'),encoding='utf8')
    canonical={p:p.read_bytes() for p in sources}
    real_loader=sync._cargar_por_ruta
    def loader(path,name):
        mod=real_loader(path,name)
        if name=='ks_backends_init':mod.cargar_adaptador=lambda *a,**k:backend
        return mod
    monkeypatch.setattr(sync,'_cargar_por_ruta',loader)
    real_replace=backend.os.replace;attempts=[]
    def replace(source,destination,*args,**kwargs):
        destination=Path(destination)
        if destination.parent==projection and destination.suffix=='.md':
            attempts.append(destination)
            if len(attempts)==2:raise OSError('Owned second-entry publication failure')
        return real_replace(source,destination,*args,**kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(backend.os,'replace',replace)
        assert sync.main(argv)==1
    result=capsys.readouterr()
    assert len(attempts)==2
    assert attempts[0].read_bytes()!=old_bytes[attempts[0]]
    assert attempts[1].read_bytes()==old_bytes[attempts[1]]
    assert (projection/'manifest.json').read_bytes()==old_manifest
    assert (projection/'manifest.pending.json').exists()
    queue=cfgdir/'_sync-outbox/docs'
    assert outbox.estado(str(queue))['outbox']==1
    assert neighbor.read_bytes()==b'Unrelated bytes.\n'
    assert {p:p.read_bytes() for p in sources}==canonical
    assert 'publicación anterior intacta' not in result.err,'Partial publication was falsely reported as an intact previous publication.'
    assert 'puede haberse aplicado parcialmente' in result.err
    assert '--outbox-status' in result.err
    assert sync.main(argv)==0;capsys.readouterr()
    assert not (projection/'manifest.pending.json').exists()
    assert all('Updated' in p.read_text(encoding='utf8') for p in old_bytes)
    assert neighbor.read_bytes()==b'Unrelated bytes.\n'
    assert {p:p.read_bytes() for p in sources}==canonical
