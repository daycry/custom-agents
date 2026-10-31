#!/usr/bin/env python3
"""One explicit loopback console for registered, independent project workspaces."""
import argparse
import hmac
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler,HTTPServer
import importlib.util
from pathlib import Path
import re
import secrets
from socketserver import ThreadingMixIn
import threading

_spec=importlib.util.spec_from_file_location('control_center_common',Path(__file__).with_name('console_common.py'))
C=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(C)
REGISTRY=C.sibling('console_workspaces.py')
USE_CASES=C.sibling('console_service.py')
ASSETS=Path(__file__).resolve().parents[1]/'assets'
WORKSPACE=r'([a-z][a-z0-9]*(?:-[a-z0-9]+)*)'
PLAN=r'([a-f0-9]{16})'
SESSION=r'([a-f0-9]{32})'
MAX_BODY=64*1024
CSP="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"

class ConsoleServer(ThreadingMixIn,HTTPServer):
    daemon_threads=True
    block_on_close=False
    def __init__(self,workspaces,port=0,sessions=None):
        C.need(type(port) is int and 0<=port<=65535,'invalid_port')
        C.need(type(workspaces) is dict and 0<len(workspaces)<=32,'invalid_registry')
        self.workspaces=workspaces;self.service=USE_CASES.Service(workspaces,sessions)
        self.token=secrets.token_urlsafe(32);self.cookie_nonce=secrets.token_urlsafe(32);self.slots=threading.BoundedSemaphore(16)
        super().__init__(('127.0.0.1',port),Handler)
    def process_request(self,request,address):
        if not self.slots.acquire(blocking=False):
            try:request.sendall(b'HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
            finally:self.shutdown_request(request)
            return
        try:super().process_request(request,address)
        except Exception:self.slots.release();raise
    def process_request_thread(self,request,address):
        try:super().process_request_thread(request,address)
        finally:self.slots.release()
    def server_close(self):
        self.service.close();super().server_close()

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    server_version='custom-agents'
    sys_version=''
    def log_message(self,*args):pass
    def setup(self):
        super().setup();self.connection.settimeout(5)
    def _headers(self,status,raw,kind='application/json; charset=utf-8',cookie=None):
        self.send_response(status)
        for name,value in [('Content-Type',kind),('Content-Length',str(len(raw))),('Cache-Control','no-store'),
                           ('Referrer-Policy','no-referrer'),('X-Content-Type-Options','nosniff'),
                           ('Content-Security-Policy',CSP),('Connection','close')]:self.send_header(name,value)
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.close_connection=True
        if self.command!='HEAD':self.wfile.write(raw)
    def _json(self,value,status=200,cookie=None):
        raw=C.encoded(value);C.need(len(raw)<=256*1024,'response_budget',503)
        self._headers(status,raw,cookie=cookie)
    def _guard(self,write=False):
        origin=f'http://127.0.0.1:{self.server.server_port}'
        C.need(self.headers.get_all('Host')==[f'127.0.0.1:{self.server.server_port}'],'invalid_host',403)
        origins=self.headers.get_all('Origin') or []
        C.need(len(origins)<=1 and (not origins or origins[0]==origin),'invalid_origin',403)
        if write:C.need(origins==[origin],'origin_required',403)
        C.need(self.headers.get('Sec-Fetch-Site') not in ('cross-site','same-site'),'invalid_origin',403)
        C.need(not self.headers.get_all('Transfer-Encoding'),'invalid_framing')
        C.need(len(self.headers.get_all('Content-Length') or [])<=1,'invalid_framing')
        C.need(self.path.startswith('/') and len(self.path)<=1024 and not any(x in self.path for x in ('%','?','#','\\','/../','/./','//')),'invalid_route',404)
    def _auth(self):
        cookies=self.headers.get_all('Cookie') or []
        C.need(len(cookies)==1 and len(cookies[0])<=4096,'authentication_required',401)
        parsed=SimpleCookie()
        try:parsed.load(cookies[0])
        except Exception:raise C.ConsoleError('authentication_required',401) from None
        token=parsed.get('ca_console')
        C.need(token is not None and token.value.isascii() and hmac.compare_digest(token.value,self.server.cookie_nonce),'authentication_required',401)
        authorization=self.headers.get_all('Authorization') or []
        C.need(len(authorization)==1 and authorization[0].isascii() and hmac.compare_digest(authorization[0],'Bearer '+self.server.token),'authentication_required',401)
    def _body(self):
        C.need(self.headers.get('Content-Type','').lower()=='application/json','json_required',415)
        length=self.headers.get('Content-Length')
        C.need(length is not None and length.isascii() and length.isdecimal(),'invalid_framing')
        size=int(length);C.need(0<size<=MAX_BODY,'request_budget',413)
        raw=self.rfile.read(size);C.need(len(raw)==size,'incomplete_request')
        value=C.json_load(raw);C.need(type(value) is dict,'invalid_request');return value
    def _get(self):
        self._guard()
        C.need(self.headers.get('Content-Length') in (None,'0'),'invalid_framing')
        static={'/':('control-center.html','text/html; charset=utf-8'),
                '/assets/control-center.css':('control-center.css','text/css; charset=utf-8'),
                '/assets/control-center.js':('control-center.js','text/javascript; charset=utf-8')}
        for name in ('console-dom.js','console-sessions.js','console-plans.js','console-context.js'):
            static['/assets/'+name]=(name,'text/javascript; charset=utf-8')
        if self.path in static:
            name,kind=static[self.path]
            try:raw=(ASSETS/name).read_bytes()
            except OSError:raise C.ConsoleError('console_asset_unavailable',503) from None
            self._headers(200,raw,kind);return
        self._auth()
        if self.path=='/api/workspaces':
            self._json({'version':1,'workspaces':[w.public() for w in self.server.workspaces.values()]});return
        match=re.fullmatch('/api/workspaces/'+WORKSPACE+'/(.+)',self.path)
        C.need(match is not None,'route_not_found',404)
        workspace,tail=match.groups();service=self.server.service;service.workspace(workspace)
        if tail=='plans':value=service.plans(workspace)
        elif tail=='sessions':value={'sessions':service.sessions.list(workspace)}
        elif tail=='runtimes':value=service.runtimes(workspace)
        elif tail=='memory':value=service.memory(workspace)
        elif tail=='integrations':value=service.integrations(workspace)
        elif tail=='activity':value=service.activity(workspace)
        elif tail=='catalog':value=service.catalog(workspace)
        elif (part:=re.fullmatch('sessions/'+SESSION,tail)):value=service.sessions.get(workspace,part[1])
        elif (part:=re.fullmatch('plans/'+PLAN,tail)):value=service.plan(workspace,part[1])
        elif (part:=re.fullmatch('plans/'+PLAN+'/tasks/(T-[0-9]{1,4})',tail)):value=service.task(workspace,part[1],part[2])
        elif (part:=re.fullmatch('plans/'+PLAN+'/tasks/(T-[0-9]{1,4})/comments',tail)):value=service.notes(workspace,part[1],part[2])
        elif (part:=re.fullmatch('plans/'+PLAN+'/documents/(plan|spec|evaluation|design|tasks)',tail)):value=service.document(workspace,part[1],part[2])
        else:raise C.ConsoleError('route_not_found',404)
        self._json(value)
    def _post(self):
        self._guard(write=True);data=self._body()
        if self.path=='/api/bootstrap':
            C.need(set(data)=={'token'} and type(data['token']) is str and data['token'].isascii() and hmac.compare_digest(data['token'],self.server.token),'invalid_capability',403)
            self._json({'status':'authenticated'},cookie='ca_console='+self.server.cookie_nonce+'; Path=/; HttpOnly; SameSite=Strict');return
        self._auth()
        match=re.fullmatch('/api/workspaces/'+WORKSPACE+'/(.+)',self.path)
        C.need(match is not None,'route_not_found',404)
        workspace,tail=match.groups();service=self.server.service;service.workspace(workspace)
        if tail=='sessions':
            C.need(set(data)=={'runtime','title','request_id'},'invalid_session')
            value=service.sessions.create(workspace,data['runtime'],data['title'],data['request_id'])
        elif tail=='memory/query':value=service.memory_query(workspace,data)
        elif (part:=re.fullmatch('sessions/'+SESSION+'/messages',tail)):
            C.need(set(data)=={'text','request_id'},'invalid_message')
            value=service.sessions.send(workspace,part[1],data['text'],data['request_id'])
        elif (part:=re.fullmatch('sessions/'+SESSION+'/interrupt',tail)):
            C.need(data=={},'invalid_request');value=service.sessions.interrupt(workspace,part[1])
        elif (part:=re.fullmatch('sessions/'+SESSION+'/disconnect',tail)):
            C.need(data=={},'invalid_request');value=service.sessions.disconnect(workspace,part[1])
        elif (part:=re.fullmatch('sessions/'+SESSION+'/resume',tail)):
            C.need(data=={},'invalid_request');value=service.sessions.resume(workspace,part[1])
        elif (part:=re.fullmatch('sessions/'+SESSION+'/answer',tail)):
            C.need(set(data)=={'request_id','response'},'invalid_answer')
            value=service.sessions.answer(workspace,part[1],data['request_id'],data['response'])
        elif (part:=re.fullmatch('plans/'+PLAN+'/tasks/(T-[0-9]{1,4})/comments',tail)):value=service.notes(workspace,part[1],part[2],data)
        elif (part:=re.fullmatch('plans/'+PLAN+'/prepare',tail)):
            C.need(set(data)=={'action','task'},'invalid_plan_action')
            value=service.prepare(workspace,part[1],data['action'],data['task'])
        elif (part:=re.fullmatch('plans/'+PLAN+'/run',tail)):value=service.run_plan(workspace,part[1],data)
        else:raise C.ConsoleError('route_not_found',404)
        self._json(value)
    def _handle(self,operation):
        try:operation()
        except ValueError as error:
            try:self._json({'error':getattr(error,'code','request_unavailable')},getattr(error,'status',400))
            except (OSError,ValueError):pass
        except (OSError,TimeoutError):
            try:self._json({'error':'request_unavailable'},503)
            except OSError:pass
        except Exception:
            try:self._json({'error':'service_unavailable'},503)
            except OSError:pass
    def do_GET(self):self._handle(self._get)
    def do_HEAD(self):self._handle(self._get)
    def do_POST(self):self._handle(self._post)
    def do_PUT(self):self._headers(405,b'')
    do_DELETE=do_PUT
    do_PATCH=do_PUT
    do_OPTIONS=do_PUT


def create_server(workspaces,*,port=0,sessions=None):return ConsoleServer(workspaces,port,sessions)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    source=parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--workspaces',help='explicit versioned workspace registry JSON')
    source.add_argument('--project',help='single project, served by the same console')
    parser.add_argument('--port',type=int,default=8769)
    args=parser.parse_args(argv)
    server=None
    try:
        if args.workspaces:workspaces=REGISTRY.load_workspaces(args.workspaces)
        else:
            root=C.safe_root(str(Path(args.project).absolute()))
            workspaces={'project':REGISTRY.Workspace('project',root.name,root,C.RUNTIMES)}
        server=create_server(workspaces,port=args.port)
        print(f'custom-agents dashboard: http://127.0.0.1:{server.server_port}/#token={server.token}',flush=True)
        server.serve_forever(poll_interval=.2)
    except KeyboardInterrupt:return 0
    except (ValueError,OSError):
        print('custom-agents dashboard: startup unavailable; check registry, project and port.',flush=True);return 2
    finally:
        if server:server.server_close()
    return 0

if __name__=='__main__':raise SystemExit(main())
