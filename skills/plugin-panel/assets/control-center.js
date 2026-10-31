import {$,el,icon,button,badge,providers,key,loading,empty,busy} from './console-dom.js'
import {createSessions} from './console-sessions.js'
import {createPlans} from './console-plans.js'
import {createContext} from './console-context.js'

const titles={
 overview:['TU CENTRO DE TRABAJO','Todo listo para avanzar.','Conversaciones, planes y contexto. Cada cosa en su proyecto.','Vista general'],
 sessions:['CONVERSACIONES CON TU EQUIPO','Del objetivo a la acción.','Trabaja con tu entorno nativo y conserva el hilo de cada iniciativa.','Sesiones'],
 plans:['CARTERA DEL PROYECTO','Una visión clara del trabajo.','Planes, fases y tareas con estados contrastados en el proyecto.','Planes y tareas'],
 plan:['PLAN DE TRABAJO','Cada paso, con contexto.','Criterios, revisión, pruebas y notas para saber qué falta.','Detalle de plan'],
 activity:['ACTIVIDAD OBSERVADA','Mira cómo avanza el trabajo.','Sesiones, agentes y operaciones con su procedencia y última señal.','Agentes en vivo'],
 memory:['CONOCIMIENTO DEL PROYECTO','Lo aprendido sigue contigo.','Decisiones, reglas y aprendizajes; memoria local e integraciones opcionales.','Memoria'],
 integrations:['HERRAMIENTAS DEL EQUIPO','Conecta lo que tu proyecto necesita.','Entornos de ejecución, seguimiento y memoria, con sus límites visibles.','Integraciones'],
 catalog:['CAPACIDADES A TU ALCANCE','El especialista adecuado, a mano.','Explora agentes, skills, comandos y las ampliaciones de este proyecto.','Capacidades']}
const errors={
 authentication_required:'Vuelve a abrir el enlace de arranque para conectar con el servidor.',
 session_busy:'La sesión está ocupada. Atiende su solicitud o espera a que termine.',
 runtime_not_installed:'No se ha encontrado el ejecutable nativo. Revisa su instalación en este equipo.',
 native_start_failed:'No se pudo iniciar el entorno nativo. Revisa su instalación y autenticación.',
 native_start_timeout:'El entorno no terminó de prepararse dentro del plazo. Revisa su estado antes de repetir.',
 native_scope_mismatch:'El entorno devolvió un proyecto distinto. La operación se ha bloqueado.',
 project_changed:'La carpeta del proyecto ha cambiado. Revisa el registro y reinicia la consola.',
 plan_changed:'El plan cambió desde la vista previa. Revisa la versión actual antes de enviar.',
 version_changed:'Las notas cambiaron. Se conserva tu texto; actualiza antes de guardarlo.',
 request_conflict:'Esta petición ya se utilizó con otro contenido. Comprueba lo que se recibió.',
 session_state_unavailable:'El registro de sesiones necesita revisión; no se sobrescribirá.',
 session_budget:'Has alcanzado el límite de sesiones de esta consola. Desconecta las que no necesites.',
 delivery_uncertain:'No se ha podido confirmar el envío. Comprueba la sesión antes de repetir.',
 decision_uncertain:'No se ha confirmado la respuesta. Comprueba el estado en el entorno nativo.',
 native_request_failed:'El entorno nativo rechazó la operación. Revisa su autenticación y compatibilidad.',
 native_v2_required:'Esta conexión necesita una API compatible de OpenCode 2.',
 document_unavailable:'Este documento no está disponible en el plan.',
 task_unavailable:'No se ha podido leer el detalle de esta tarea.',
 response_budget:'El resultado supera el límite de esta vista. Acota el alcance.',
 service_unavailable:'No se pudo preparar esta vista. Actualiza y revisa el diagnóstico si se repite.'}

const accessStorageKey='custom-agents-console-access-v1'
let apiAccessToken=''
try{apiAccessToken=sessionStorage.getItem(accessStorageKey)||''}catch{}
class Stale extends Error{}
const state={workspace:null,epoch:0,view:'overview',navigation:0,workspaces:[],sessions:[],runtimes:[],portfolio:null,
 plan:null,controllers:new Set(),booting:false,ready:false,pendingRun:null}
const ideaDrafts=new Map()
const app={state,$,Stale}
app.explain=error=>errors[error?.code]||(error?.name==='AbortError'?'La lectura no terminó. Puedes actualizar sin reenviar trabajo.':'No se pudo completar la operación. Revisa el estado antes de repetir.')
app.notice=(text,kind='')=>{const box=$('view-banner');box.textContent=text||'';box.className='notice '+kind;box.hidden=!text}
let toastTimer
app.toast=(text,error=false)=>{const box=$('toast');box.textContent=text;box.className='toast'+(error?' error':'');box.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>{box.hidden=true},6500)}
app.safe=fn=>async(...args)=>{try{return await fn(...args)}catch(error){if(error instanceof Stale)return;app.toast(app.explain(error),true)}}
function gate(){
 state.ready=false;$('auth-gate').hidden=false;$('app-shell').inert=true
 $('auth-message').textContent='La conexión local necesita el enlace del servidor.'
}
async function fetchJSON(path,{method='GET',body,scoped=true}={}){
 const epoch=state.epoch,controller=new AbortController();state.controllers.add({controller,method})
 const timeout=setTimeout(()=>controller.abort(),30000)
 try{
  const response=await fetch(path,{method,credentials:'same-origin',signal:controller.signal,
   headers:{...(apiAccessToken?{Authorization:'Bearer '+apiAccessToken}:{}),...(body===undefined?{}:{'Content-Type':'application/json'})},body:body===undefined?undefined:JSON.stringify(body)})
  const raw=await response.text()
  if(scoped&&epoch!==state.epoch)throw new Stale()
  if(raw.length>1024*1024)throw Object.assign(new Error(),{code:'response_budget'})
  let data
  try{data=JSON.parse(raw)}catch{throw Object.assign(new Error(),{code:'service_unavailable'})}
  if(!response.ok){
   if(response.status===401)gate()
   throw Object.assign(new Error(),{code:data.error||'service_unavailable',status:response.status})
  }
  $('connection-status').textContent='Conectado';$('connection-status').className='connection-state connected'
  return data
 }catch(error){
  if(scoped&&epoch!==state.epoch)throw new Stale()
  $('connection-status').textContent='Sin confirmar';$('connection-status').className='connection-state failed'
  throw error
 }finally{
  clearTimeout(timeout)
  for(const item of state.controllers)if(item.controller===controller)state.controllers.delete(item)
 }
}
app.api=(tail,options={})=>{
 if(!state.workspace)throw new Stale()
 return fetchJSON('/api/workspaces/'+encodeURIComponent(state.workspace)+'/'+tail,options)
}
app.observed=value=>{if(value)$('last-observed').textContent='Última observación · '+new Date(value).toLocaleTimeString('es',{hour:'2-digit',minute:'2-digit',second:'2-digit'})}
app.openDialog=id=>{const node=$(id);node.returnFocus=document.activeElement;if(!node.open)node.showModal()}
app.closeDialog=id=>{if($(id).open)$(id).close()}
app.sessions=createSessions(app)
app.plans=createPlans(app)
app.context=createContext(app)

function route(){
 const query=new URLSearchParams()
 if(state.workspace)query.set('workspace',state.workspace)
 query.set('view',state.view)
 if(state.view==='plan'&&state.plan)query.set('plan',state.plan)
 history.replaceState(null,'',location.pathname+'#'+query)
}
app.navigate=async(view,{plan=null,session=null,focus=true}={})=>{
 if(!titles[view])view='overview'
 state.navigation++;state.view=view
 if(plan)state.plan=plan
 for(const [name] of Object.entries(titles))$('view-'+name).hidden=name!==view
 document.querySelectorAll('[data-view]').forEach(node=>{
  const active=node.dataset.view===(view==='plan'?'plans':view)
  if(active)node.setAttribute('aria-current','page');else node.removeAttribute('aria-current')
 })
 const [kicker,title,description,breadcrumb]=titles[view]
 $('view-kicker').textContent=kicker;$('view-title').textContent=title;$('view-description').textContent=description
 $('breadcrumb-view').textContent=breadcrumb
 document.title=breadcrumb+' · custom-agents'
 app.notice('')
 if(mobileDialog.open)mobileDialog.close()
 route()
 if(focus)$('main').focus({preventScroll:true})
 if(session)state.selectedSession=session
 await refresh()
}
let refreshing=false
async function refresh(){
 if(!state.ready)return
 const navigation=state.navigation
 try{
  switch(state.view){
   case 'overview':await app.context.overview();break
   case 'sessions':await app.sessions.refresh();break
   case 'plans':await app.plans.load();break
   case 'plan':await app.plans.detail();break
   case 'activity':await app.context.activity();break
   case 'memory':await app.context.memory();break
   case 'integrations':await app.context.integrations();break
   case 'catalog':await app.context.catalog();break
  }
 }catch(error){
  if(error instanceof Stale||navigation!==state.navigation)return
  app.notice(app.explain(error),'error')
 }
}
app.refresh=refresh
async function chooseWorkspace(id,{view=null,plan=null}={}){
 if(!state.workspaces.some(w=>w.id===id))return
 if(state.workspace)ideaDrafts.set(state.workspace,{title:$('idea-name').value,goal:$('idea-goal').value})
 app.sessions.clear()
 for(const item of state.controllers)if(item.method==='GET')item.controller.abort()
 state.epoch++;state.navigation++;state.workspace=id;state.selectedSession=null;state.sessions=[];state.runtimes=[];state.portfolio=null;state.plan=null;state.pendingRun=null
 app.runRequest=null
 const idea=ideaDrafts.get(id)
 $('idea-name').value=idea?.title||'';$('idea-goal').value=idea?.goal||''
 $('session-search').value='';$('plan-search').value='';$('plan-filter').value='all'
 $('last-observed').textContent='Esperando datos de este proyecto'
 for(const dialog of document.querySelectorAll('dialog[open]'))dialog.close()
 const workspace=state.workspaces.find(w=>w.id===id)
 $('workspace-select').value=id;$('breadcrumb-project').textContent=workspace.name;$('workspace-avatar').textContent=workspace.name.slice(0,1).toUpperCase()
 app.plans.clear();app.context.clear();$('nav-sessions-count').textContent='—'
 const desired=view&&titles[view]&&((view!=='plan')||/^[a-f0-9]{16}$/.test(plan||''))?view:state.view==='plan'?'plans':state.view
 await app.navigate(desired,{focus:false,plan:desired==='plan'?plan:null})
}
let sessionCreating=false,sessionRequest=null,initialPrompt=''
app.newSession=async(title='',prompt='',preferredRuntime=null)=>{
 if(sessionCreating){app.toast('Ya se está abriendo una sesión. Comprueba la lista de conversaciones.');return}
 const epoch=state.epoch
 const data=await app.api('runtimes');if(epoch!==state.epoch)throw new Stale()
 state.runtimes=Array.isArray(data.runtimes)?data.runtimes:[]
 const select=$('session-runtime');select.replaceChildren()
 for(const runtime of state.runtimes){
  const option=el('option',providers[runtime.id]||runtime.id)
  option.value=runtime.id;option.disabled=!runtime.enabled||!runtime.installed
  if(option.disabled)option.textContent+=' · '+(!runtime.enabled?'no habilitado':'sin instalar')
  select.append(option)
 }
 const available=[...select.options].find(o=>!o.disabled)
 if(available)select.value=[...select.options].some(o=>o.value===preferredRuntime&&!o.disabled)?preferredRuntime:available.value
 $('session-create-submit').disabled=!available
 $('session-name').value=title;$('session-dialog-error').textContent=available?'':'No hay un entorno habilitado e instalado. Revisa Integraciones y el registro de proyectos.'
 initialPrompt=prompt;sessionRequest=key();app.openDialog('session-dialog')
}
$('session-create-form').addEventListener('submit',app.safe(async event=>{
 event.preventDefault();if(sessionCreating)return
 const epoch=state.epoch,title=$('session-name').value.trim(),runtime=$('session-runtime').value,request=sessionRequest
 if(!title)return
 sessionCreating=true;$('session-create-submit').disabled=true;$('session-name').disabled=true;$('session-runtime').disabled=true
 try{
  const result=await app.api('sessions',{method:'POST',body:{runtime,title,request_id:request}})
  if(epoch!==state.epoch)throw new Stale()
  const stillOpen=$('session-dialog').open
  app.closeDialog('session-dialog')
  if(stillOpen){
   await app.navigate('sessions',{session:result.id})
   app.sessions.draft(initialPrompt)
   if(state.pendingRun)state.pendingRun.session=result.id
  }else app.toast('La sesión se abrió. La encontrarás en Conversaciones.')
 }catch(error){
  if(!(error instanceof Stale))$('session-dialog-error').textContent=app.explain(error)+' Actualiza la lista antes de abrir otra.'
 }finally{
  sessionCreating=false;$('session-create-submit').disabled=false;$('session-name').disabled=false;$('session-runtime').disabled=false
 }
}))
$('idea-form').addEventListener('submit',app.safe(async event=>{
 event.preventDefault()
 const title=$('idea-name').value.trim(),goal=$('idea-goal').value.trim()
 if(!title||!goal)return
 app.closeDialog('idea-dialog')
 const prompt='Prepara una iniciativa de custom-agents para este objetivo: '+title+'.\n'+goal+
  '\nAclara los requisitos, evalúa opciones y esfuerzo y presenta un plan comprensible con criterios de aceptación. No implementes hasta que el alcance y las decisiones necesarias estén acordados.'
 await app.newSession(title,prompt)
}))
app.run=async(plan,action='continue',task=null)=>{
 const data=await app.api('plans/'+plan+'/prepare',{method:'POST',body:{action,task}})
 const sessions=await app.api('sessions');state.sessions=sessions.sessions||[]
 const available=state.sessions.filter(s=>['idle','interrupted'].includes(s.status))
 const select=$('run-session');select.replaceChildren()
 for(const session of available){const option=el('option',session.title+' · '+providers[session.runtime]);option.value=session.id;select.append(option)}
 $('run-prompt').textContent=data.prompt;$('run-error').textContent=''
 $('run-help').replaceChildren(document.createTextNode('Se enviará a una sesión disponible de este proyecto.'))
 if(!available.length){
  $('run-help').replaceChildren(document.createTextNode('Primero necesitas una sesión conectada. '))
  $('run-help').append(button('Crear una sesión para este plan',app.safe(async()=>{
   app.closeDialog('run-dialog');state.pendingRun={plan,action,task,workspace:state.workspace,session:null}
   await app.newSession('Plan · '+(state.portfolio?.iniciativas?.find(p=>p.id===plan)?.titulo||'Trabajo del proyecto'))
  }),'quiet'))
 }
 $('run-submit').disabled=!available.length
 app.runRequest={plan,action,task,preview:data,key:key(),workspace:state.workspace}
 app.openDialog('run-dialog')
}
app.sessionReady=app.safe(async session=>{
 const pending=state.pendingRun
 if(pending&&pending.workspace===state.workspace&&pending.session===session.id&&session.status==='idle'){
  state.pendingRun=null;await app.run(pending.plan,pending.action,pending.task)
 }
})
$('run-form').addEventListener('submit',app.safe(async event=>{
 event.preventDefault();const run=app.runRequest
 if(!run||run.workspace!==state.workspace)return
 $('run-submit').disabled=true
 try{
  const selected=$('run-session').value
  const data=await app.api('plans/'+run.plan+'/run',{method:'POST',body:{action:run.action,task:run.task,context_sha256:run.preview.context_sha256,session_id:selected,request_id:run.key}})
  app.closeDialog('run-dialog');await app.navigate('sessions',{session:data.id})
 }catch(error){
  if(error instanceof Stale)return
  $('run-error').textContent=app.explain(error)
  if(error.code==='plan_changed'){
   const preview=await app.api('plans/'+run.plan+'/prepare',{method:'POST',body:{action:run.action,task:run.task}})
   run.preview=preview;run.key=key();$('run-prompt').textContent=preview.prompt
  }
 }finally{$('run-submit').disabled=false}
}))

const mobileDialog=el('dialog',undefined,'mobile-navigation')
mobileDialog.setAttribute('aria-label','Navegación del proyecto');document.body.append(mobileDialog)
const sidebar=$('sidebar'),placeholder=document.createComment('sidebar'),mobileClose=button('Cerrar navegación',()=>mobileDialog.close(),'quiet')
mobileClose.className='icon-button mobile-navigation-close';mobileClose.setAttribute('aria-label','Cerrar navegación');mobileClose.replaceChildren(icon('close'))
sidebar.before(placeholder);sidebar.append(mobileClose)
function resizeNavigation(){
 const small=matchMedia('(max-width:760px)').matches
 mobileClose.hidden=!small
 if(small&&sidebar.parentNode!==mobileDialog){mobileDialog.append(sidebar);mobileClose.hidden=false}
 else if(!small&&sidebar.parentNode===mobileDialog){mobileDialog.close();placeholder.after(sidebar);mobileClose.hidden=true}
}
resizeNavigation();addEventListener('resize',resizeNavigation)
$('mobile-menu').addEventListener('click',()=>{mobileDialog.showModal();$('mobile-menu').setAttribute('aria-expanded','true')})
mobileDialog.addEventListener('close',()=>{$('mobile-menu').setAttribute('aria-expanded','false');$('mobile-menu').focus()})
document.querySelectorAll('.dialog-close').forEach(node=>node.addEventListener('click',()=>node.closest('dialog').close()))
document.querySelectorAll('dialog.dialog').forEach(node=>node.addEventListener('close',()=>{
 const target=node.returnFocus
 if(target?.isConnected&&!target.closest('[hidden]'))target.focus({preventScroll:true})
}))
document.querySelectorAll('[data-view]').forEach(node=>node.addEventListener('click',app.safe(()=>app.navigate(node.dataset.view))))
$('workspace-select').addEventListener('change',app.safe(event=>chooseWorkspace(event.target.value)))
$('new-session-button').addEventListener('click',app.safe(()=>app.newSession()))
$('session-add').addEventListener('click',app.safe(()=>app.newSession()))
$('new-plan-button').addEventListener('click',()=>app.openDialog('idea-dialog'))
$('help-button').addEventListener('click',()=>app.openDialog('help-dialog'))
$('refresh-button').addEventListener('click',app.safe(refresh))
$('theme-button').addEventListener('click',()=>{
 const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=theme
 try{localStorage.setItem('custom-agents-ui-theme',theme)}catch{}
})
try{const theme=localStorage.getItem('custom-agents-ui-theme');if(['dark','light'].includes(theme))document.documentElement.dataset.theme=theme}catch{}
function palette(){
 const query=$('palette-search').value.toLowerCase();const root=$('palette-results');root.replaceChildren()
 const actions=[['Nueva sesión',()=>app.newSession(),'plus'],['Nuevo plan',()=>app.openDialog('idea-dialog'),'board'],
  ...Object.entries(titles).filter(([id])=>id!=='plan').map(([id,value])=>[value[3],()=>app.navigate(id),'arrow']),
  ...state.workspaces.map(w=>['Proyecto · '+w.name,()=>chooseWorkspace(w.id),'grid'])]
 for(const [label,fn,symbol] of actions.filter(a=>a[0].toLowerCase().includes(query)).slice(0,14)){
  const item=button(label,app.safe(async()=>{app.closeDialog('palette-dialog');await fn()}),'quiet',symbol)
  item.className='palette-item';root.append(item)
 }
}
function openPalette(){$('palette-search').value='';palette();app.openDialog('palette-dialog');$('palette-search').focus()}
$('palette-trigger').addEventListener('click',openPalette)
$('palette-search').addEventListener('input',palette)
$('palette-search').addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();$('palette-results').querySelector('button')?.click()}})
addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();openPalette()}})
document.querySelector('.brand').addEventListener('click',app.safe(async event=>{event.preventDefault();await app.navigate('overview')}))
$('auth-retry').addEventListener('click',()=>boot())
async function boot(){
 if(state.booting)return;state.booting=true
 try{
  const params=new URLSearchParams(location.hash.slice(1)),token=params.get('token'),desired=params.get('workspace'),view=params.get('view'),plan=params.get('plan')
  if(token){
   apiAccessToken=token
   await fetchJSON('/api/bootstrap',{method:'POST',body:{token},scoped:false})
   try{sessionStorage.setItem(accessStorageKey,token)}catch{}
   params.delete('token');history.replaceState(null,'',location.pathname+(params.size?'#'+params:''))
  }
  const result=await fetchJSON('/api/workspaces',{scoped:false})
  state.workspaces=(result.workspaces||[]).filter(w=>typeof w.id==='string'&&typeof w.name==='string')
  if(!state.workspaces.length)throw Object.assign(new Error(),{code:'service_unavailable'})
  $('workspace-select').replaceChildren(...state.workspaces.map(w=>{const option=el('option',w.name);option.value=w.id;return option}))
  $('auth-gate').hidden=true;$('app-shell').inert=false;state.ready=true
  const registered=state.workspaces.some(w=>w.id===desired)
  await chooseWorkspace(registered?desired:state.workspaces[0].id,{view:registered?view:null,plan:registered?plan:null})
 }catch(error){gate();$('auth-message').textContent=app.explain(error)}
 finally{state.booting=false}
}
async function poll(){
 if(state.ready&&!document.hidden&&!refreshing&&!document.querySelector('dialog[open]')){
  refreshing=true;try{await refresh()}finally{refreshing=false}
 }
 setTimeout(poll,2000)
}
await boot();poll()

