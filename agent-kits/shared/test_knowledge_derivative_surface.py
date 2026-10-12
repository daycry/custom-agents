"""Actual graph output keeps source status distinct from derived text authority."""
from pathlib import Path
import copy,importlib.util,json
import pytest
HERE=Path(__file__).resolve().parent
def load():
    spec=importlib.util.spec_from_file_location('derived_read_surface',HERE/'knowledge-find.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def hit():return copy.deepcopy(json.loads((HERE/'fixtures/graphiti-derived-read.json').read_bytes())['aciertos'][0])

def test_native_derived_flags_survive_normalization_and_json():
    mod=load();raw=hit();normalized=mod.acierto_remoto(raw,'graph-memory')
    assert normalized is not None
    output=mod.acierto_json(normalized)
    assert output['estado']=='aprobado' and output['version']=='2'
    assert output['contenido_derivado'] is True and output['autoridad']=='ninguna'
    assert output['verificacion']=='no_verificada' and output['citas_por_afirmacion'] is False
    assert output['uuid']==raw['uuid']

def test_compact_agent_and_human_output_exposes_derived_authority():
    mod=load();normalized=mod.acierto_remoto(hit(),'graph-memory')
    line=mod.linea_compacta(normalized)
    assert 'derivado' in line and 'sin autoridad' in line and 'aprobado' in line
    assert len(line)<=mod.LINEA_MAX

@pytest.mark.parametrize('field,value',[('contenido_derivado',1),('contenido_derivado',False),
    ('autoridad','normativa'),('verificacion','verificada'),('citas_por_afirmacion',True)])
def test_inconsistent_derived_claim_is_discarded(field,value):
    mod=load();raw=hit();raw[field]=value
    assert mod.acierto_remoto(raw,'graph-memory') is None

def test_incomplete_derived_contract_cannot_lose_its_label():
    mod=load();raw=hit();del raw['contenido_derivado']
    assert mod.acierto_remoto(raw,'graph-memory') is None

def test_local_source_keeps_its_existing_shape_and_line():
    mod=load();raw=hit()
    for field in ('contenido_derivado','autoridad','verificacion','citas_por_afirmacion','uuid'):raw.pop(field)
    normalized=mod.acierto_remoto(raw,'documents')
    assert normalized is not None
    output=mod.acierto_json(normalized)
    assert 'contenido_derivado' not in output and 'derivado' not in output['linea']


def test_long_identity_cannot_truncate_the_derived_authority_label():
    mod=load();raw=hit();raw['id']='source.'+'x'*190
    normalized=mod.acierto_remoto(raw,'graph-memory')
    line=mod.linea_compacta(normalized)
    assert line.startswith('derivado sin autoridad') and len(line)<=mod.LINEA_MAX


def test_derived_source_identity_is_preserved_exactly_in_json():
    mod=load();raw=hit();raw['id']='source.'+'x'*250
    raw['ruta']='docs/knowledge/approved/gotchas/'+'a'*220+'.md'
    normalized=mod.acierto_remoto(raw,'graph-memory')
    assert normalized is not None
    result=mod.acierto_json(normalized)
    assert result['id']==raw['id'] and result['ruta']==raw['ruta']


@pytest.mark.parametrize('field,value',[('id','source.'+'x'*510),('ruta','docs/knowledge/'+'a'*4100),
    ('id','source\u202ehidden'),('ruta','docs/knowledge/approved/\u202ehidden.md')])
def test_invalid_derived_identity_is_rejected_instead_of_changed(field,value):
    mod=load();raw=hit();raw[field]=value
    assert mod.acierto_remoto(raw,'graph-memory') is None
