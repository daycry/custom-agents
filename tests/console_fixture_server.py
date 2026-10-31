"""Explicit browser-QA fixture; never imported by the product."""
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import threading
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'skills/plugin-panel/scripts'
WORKSPACES=(('portal','Portal · datos de prueba'),('billing','Facturación · datos de prueba'))

def load(name):
    spec=importlib.util.spec_from_file_location('fixture_'+name.replace('.','_'),SCRIPTS/name)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class FixtureDriver:
    def __init__(self,workspace,runtime,emit):
        self.workspace,self.emit=workspace,emit;self.seq=0
    def start(self,resume_id=None):
        self.emit({'type':'capabilities','agents':['implementer','qa'],'skills':['tdd'],'tools':['Read','Write'],'mcp':['project-wiki']})
        return resume_id or 'fixture-'+self.workspace.id
    def send(self,text):
        self.seq+=1
        self.emit({'type':'status','status':'running'})
        self.emit({'type':'tool','id':str(self.seq),'name':'Read','state':'completed','actor':'implementer'})
        if 'ask-permission' in text:
            self.emit({'type':'approval','id':'fixture-approval','title':'Escribir el archivo de prueba','preview':'pilot.txt','choices':['allow','deny']})
            return
        self.emit({'type':'message','id':'reply-'+str(self.seq),'role':'assistant','text':'Respuesta de prueba: '+text})
        self.emit({'type':'status','status':'idle'})
    def answer(self,key,payload):
        self.emit({'type':'message','id':'permission-reply','role':'assistant','text':'Decisión de prueba recibida.'})
        self.emit({'type':'status','status':'idle'})
    def interrupt(self):self.emit({'type':'status','status':'interrupted'})
    def close(self):pass

def main():
    if sys.argv[1:]==['--describe']:
        print(json.dumps({'fixture':True,'workspaces':[{'id':ident,'name':name} for ident,name in WORKSPACES]},ensure_ascii=False),flush=True)
        return
    root=Path(tempfile.mkdtemp(prefix='custom-agents-console-browser-'))
    registry=load('console_workspaces.py');workspaces={}
    for ident,name in WORKSPACES:
        project=root/ident
        for slug,title in [('2026-10-31-portal','Portal de solicitudes'),('2026-10-30-reporting','Informe mensual')]:
            initiative=project/'docs/roadmap'/slug;initiative.mkdir(parents=True)
            (initiative/'spec.md').write_text('---\nestado: aprobada\n---\n# '+title+'\n\nPermitir decisiones con motivo y permisos.\n',encoding='utf-8')
            (initiative/'improvement-plan.md').write_text('# '+title+'\n\n## Objetivo\n\nEntregar un recorrido verificable para el equipo.\n',encoding='utf-8')
            (initiative/'tasks.md').write_text(
                '---\nestado: en-progreso\n---\n# '+title+'\n\n## Fase 1 — Preparar y ejecutar\n\n'
                '### T-01 — Comprobar permisos del responsable\n\n- **Estado**: completado\n- **Tipo**: backend\n- **Descripción**: Autorizar la decisión solo al responsable.\n- **Verificación**: Pruebas del proyecto.\n\n**Criterios de aceptación**\n- [x] Una persona ajena recibe un rechazo.\n\n'
                '### T-02 — Aprobar o rechazar con motivo\n\n- **Estado**: en-progreso\n- **Tipo**: backend\n- **Descripción**: Evitar la doble decisión y exigir un motivo.\n- **Verificación**: Casos de aceptación.\n\n**Criterios de aceptación**\n- [ ] Un rechazo vacío mantiene la solicitud pendiente.\n\n'
                '### T-03 — Revisar la experiencia del equipo\n\n- **Estado**: en-revision\n- **Tipo**: frontend\n- **Descripción**: Comprobar claridad y teclado.\n\n'
                '### T-04 — Compartir la guía de uso\n\n- **Estado**: borrador\n- **Tipo**: docs\n- **Descripción**: Guía detallada para responsables.\n',
                encoding='utf-8')
        workspaces[ident]=registry.Workspace(ident,name,project,('codex',))
        if ident=='portal':
            knowledge=project/'docs/knowledge/adr';knowledge.mkdir(parents=True)
            (knowledge/'ADR-101-portal.md').write_text('---\nid: ADR-101\ntitulo: Motivo obligatorio del portal\nestado: aceptada\nfecha: 2026-10-31\narea: Portal\n---\n\n# Motivo obligatorio del portal\n\nEl rechazo conserva un motivo verificable.\n',encoding='utf-8')
            custom=project/'.claude/skills/portal-policy';custom.mkdir(parents=True)
            (custom/'SKILL.md').write_text('---\nname: portal-policy\ndescription: Revisa reglas del portal.\n---\n\nPrivate fixture instructions.\n',encoding='utf-8')
            (project/'.claude/integrations.json').write_text(json.dumps({'version':1,'bindings':[{
                'id':'portal-wiki','purpose':'documentation','enabled':True,'contract_version':1,
                'adapter':{'kind':'tool','name':'project-wiki.publish','origin':'session'},
                'events':[],'capabilities':['publish']}]}),encoding='utf-8')
    sessions=load('console_sessions.py').SessionManager(workspaces,factory=FixtureDriver)
    server=load('control_center.py').create_server(workspaces,port=0,sessions=sessions)
    # Fixture availability must not depend on native tools installed on the QA host.
    server.service.runtimes=lambda ident:{'runtimes':[{'id':'codex','enabled':True,'installed':True,
        'connection':'fixture','capabilities':{'chat':True,'resume_known':True,'interrupt':True,'approval':True}}]}
    print(json.dumps({'url':f'http://127.0.0.1:{server.server_port}/#token={server.token}','fixture':True}),flush=True)
    try:server.serve_forever(poll_interval=.1)
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()

