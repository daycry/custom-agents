import {$,el,icon,button,badge,provider,providers,busy,relative,time,empty,markdown} from './console-dom.js'

export function createSessions(app){
 const state=app.state,drafts=new Map()
 let activeKey=null,current=null,messageSignature='',requestSignature='',listSignature='',refreshSequence=0,pendingSend=null
 function saveDraft(){if(activeKey)drafts.set(activeKey,$('chat-input').value)}
 function clear(){
  saveDraft();activeKey=null;current=null;messageSignature='';requestSignature='';listSignature='';pendingSend=null;refreshSequence++
  $('chat-input').value='';$('chat-messages').replaceChildren();$('chat-requests').replaceChildren();$('session-context').replaceChildren();$('session-tools').replaceChildren();$('session-list').replaceChildren()
  $('chat-title').textContent='Tu próxima conversación';$('chat-state').textContent='Elige una sesión de este proyecto.';$('chat-provider').textContent='SESIÓN'
  $('send-button').disabled=true;$('interrupt-button').disabled=true;$('resume-session').hidden=true
 }
 async function select(id){
  if(state.selectedSession!==id){saveDraft();state.selectedSession=id;current=null;messageSignature='';requestSignature='';pendingSend=null}
  const selected=state.workspace+':'+id
  if(activeKey!==selected){activeKey=selected;$('chat-input').value=drafts.get(selected)||'';$('chat-messages').replaceChildren();$('chat-requests').replaceChildren()}
  renderList(true);await snapshot()
 }
 function draft(text){$('chat-input').value=text||'';saveDraft();updateComposer()}
 function renderList(force=false){
  const query=$('session-search').value.trim().toLowerCase()
  const sessions=state.sessions.filter(s=>s.title.toLowerCase().includes(query))
  const signature=JSON.stringify([sessions,state.selectedSession,query])
  if(!force&&signature===listSignature)return
  listSignature=signature;const root=$('session-list')
  if(!sessions.length){empty(root,'Un hilo para cada objetivo.','Abre una sesión para conversar y ejecutar trabajo en este proyecto.','chat',[],true);return}
  root.replaceChildren()
  for(const session of sessions){
   const row=el('button',undefined,'session-row'+(state.selectedSession===session.id?' selected':''))
   row.type='button';row.dataset.session=session.id;row.setAttribute('aria-label',session.title+' · '+(providers[session.runtime]||session.runtime))
   const top=el('span',undefined,'session-row-top');top.append(provider(session.runtime),el('strong',session.title))
   row.append(top,el('small',(badge(session.status).textContent)+' · '+relative(session.updated_at)))
   row.addEventListener('click',app.safe(()=>select(session.id)));root.append(row)
  }
 }
 function updateComposer(){
  const available=current&&['idle','interrupted'].includes(current.status)
  $('send-button').disabled=!available||!$('chat-input').value.trim()
  $('interrupt-button').disabled=!current||!busy.has(current.status)||['connecting','disconnecting'].includes(current.status)
  $('resume-session').hidden=!current||current.can_resume!==true
  $('disconnect-session').disabled=!current||current.can_disconnect!==true
  if(current?.status==='uncertain')$('composer-hint').textContent='Resultado por confirmar · revisa el estado antes de reenviar'
  else if(current?.status==='waiting')$('composer-hint').textContent='Atiende la solicitud de la sesión para continuar'
  else if(current&&busy.has(current.status))$('composer-hint').textContent='Puedes preparar el siguiente mensaje mientras esperas'
  else $('composer-hint').textContent='Enter para enviar · Mayús + Enter para otra línea'
 }
 function inspector(session){
  const root=$('session-context');root.replaceChildren()
  const available=session.capabilities||{}
  for(const [key,label] of [['agents','Agentes disponibles'],['skills','Skills disponibles'],['tools','Herramientas disponibles'],['mcp','Servidores MCP declarados']]){
   const section=el('div',undefined,'context-section');section.append(el('h4',label))
   const values=Array.isArray(available[key])?available[key]:[]
   if(values.length){const list=el('div',undefined,'pill-list');for(const value of values.slice(0,30))list.append(el('span',value,'pill'));section.append(list)
    if(values.length>30)section.append(el('p','Y '+(values.length-30)+' más declaradas.','small-muted'))}
   else section.append(el('p','Sin declaración recibida.','small-muted'))
   root.append(section)
  }
  const operations=$('session-tools');operations.replaceChildren()
  const latest=new Map()
  for(const event of session.events||[])latest.set(event.id,event)
  for(const event of [...latest.values()].slice(-12).reverse()){
   const row=el('div',undefined,'tool-row '+event.state),copy=el('div')
   row.append(icon(event.state==='failed'?'close':event.state==='started'?'clock':'check'))
   copy.append(el('strong',event.name),el('small',(event.actor||'Rol no informado')+' · '+time(event.at)))
   row.append(copy);operations.append(row)
  }
  if(!latest.size)operations.append(el('p','Todavía no hay operaciones observadas.','small-muted'))
 }
 function renderMessages(session){
  const signature=JSON.stringify([session.messages,session.truncated,session.status])
  if(signature===messageSignature)return
  messageSignature=signature;const root=$('chat-messages')
  const bottom=root.scrollHeight-root.scrollTop-root.clientHeight<100||!root.querySelector('.chat-message')
  if(!session.messages?.length){
   empty(root,session.status==='connecting'?'Preparando tu entorno…':'¿Por dónde empezamos?',
    session.status==='connecting'?'La conexión está en preparación. Puedes escribir tu objetivo mientras esperas.':'Explica tu objetivo, pide un plan o continúa una tarea. Los permisos del entorno siguen vigentes.','chat')
   return
  }
  const existing=new Map([...root.querySelectorAll('.chat-message')].map(n=>[n.dataset.message,n]))
  const desired=[]
  for(const message of session.messages){
   let row=existing.get(message.id)
   if(!row){
    row=el('article',undefined,'chat-message '+(message.role==='user'?'user':'assistant'));row.dataset.message=message.id
    const avatar=el('span',message.role==='user'?'TÚ':'AI','chat-message-avatar')
    const header=el('header',undefined,'chat-message-header');header.append(el('span',message.role==='user'?'Tú':providers[session.runtime]||'Asistente'),el('time',time(message.created_at)))
    row.append(avatar,header,el('div',undefined,'message-body'))
   }
   if(row._text!==message.text){row.querySelector('.message-body').replaceChildren(markdown(message.text));row._text=message.text}
   desired.push(row)
  }
  if(session.truncated)desired.unshift(el('p','Vista acotada de mensajes y operaciones. La historia nativa se conserva en su entorno.','small-muted'))
  root.replaceChildren(...desired);if(bottom)root.scrollTop=root.scrollHeight
 }
 function renderRequests(session){
  const signature=JSON.stringify(session.pending||[])
  const root=$('chat-requests')
  if(signature===requestSignature&&![...root.children].some(node=>node._needsReconcile))return
  requestSignature=signature
  const existing=new Map([...root.querySelectorAll('.request-card')].map(node=>[node.dataset.request,node])),desired=[]
  for(const request of session.pending||[]){
   const requestJSON=JSON.stringify(request),previous=existing.get(request.id)
   if(previous?._requestJSON===requestJSON){
    if(previous._needsReconcile){for(const node of previous.querySelectorAll('button'))node.disabled=false;previous._needsReconcile=false}
    desired.push(previous);continue
   }
   const box=el('form',undefined,'request-card');box.dataset.request=request.id
   box._requestJSON=requestJSON
   box.append(el('h3',request.title||'La sesión necesita tu respuesta'))
   if(request.preview)box.append(el('pre',request.preview))
   if(request.truncated)box.append(el('p','La vista previa está recortada. Revisa la operación en el entorno nativo antes de permitirla.','small-muted'))
   const inputs=new Map()
   for(const field of request.fields||[]){
    const id='question-'+Math.random().toString(36).slice(2),label=el('label',field.label);label.htmlFor=id
    let input
    if(field.options?.length){
     input=el('select');input.append(el('option','Elige una respuesta'))
     input.options[0].value='';input.required=true
     for(const option of field.options){const node=el('option',option);node.value=option;input.append(node)}
    }else{input=el('input');input.type='text';input.required=true;input.maxLength=2000}
    input.id=id;inputs.set(field.id,input);box.append(label,input)
   }
   const error=el('p',undefined,'form-error');error.setAttribute('role','status')
   const actions=el('div',undefined,'request-actions')
   async function answer(payload){
    if(box._submitting)return
    box._submitting=true
    const id=session.id,workspace=state.workspace
    for(const node of box.querySelectorAll('button'))node.disabled=true
    try{
     await app.api('sessions/'+id+'/answer',{method:'POST',body:{request_id:request.id,response:payload}})
     if(workspace!==state.workspace||state.selectedSession!==id)return
     await snapshot()
    }catch(reason){
     if(reason instanceof app.Stale)return
     if(workspace!==state.workspace||state.selectedSession!==id)return
     box._needsReconcile=true;box._submitting=false
     error.textContent=app.explain(reason);app.toast(app.explain(reason),true)
     // Only a fresh server snapshot can re-enable an unconsumed request.
     try{await snapshot()}catch{}
    }finally{box._submitting=false}
   }
   for(const choice of request.choices||[]){
    if(choice==='submit'){
     const submit=button('Enviar respuesta',null,'primary');submit.type='submit';actions.append(submit)
    }else{
     const label={allow:'Permitir una vez',deny:'Rechazar',cancel:'Cancelar solicitud'}[choice]||choice
     const action=button(label,app.safe(()=>answer({decision:choice})),choice==='allow'?'primary':'secondary')
     action.dataset.decision=choice;actions.append(action)
    }
   }
   box.addEventListener('submit',app.safe(async event=>{
    event.preventDefault()
    if(!box.reportValidity())return
    await answer({answers:Object.fromEntries([...inputs].map(([id,input])=>[id,input.value]))})
   }))
   box.append(error,actions);desired.push(box)
  }
  root.replaceChildren(...desired)
 }
 async function snapshot(){
  const id=state.selectedSession;if(!id)return
  const sequence=++refreshSequence
  const result=await app.api('sessions/'+id)
  if(sequence!==refreshSequence||state.selectedSession!==id||state.view!=='sessions')return
  current=result;$('chat-title').textContent=result.title;$('chat-provider').textContent=providers[result.runtime]||result.runtime
  $('chat-state').replaceChildren(badge(result.status))
  if(result.error)$('chat-state').append(document.createTextNode(' · '+(app.explain({code:result.error}))))
  renderMessages(result);renderRequests(result);inspector(result);updateComposer()
  await app.sessionReady(result)
 }
 async function refresh(){
  const result=await app.api('sessions');state.sessions=Array.isArray(result.sessions)?result.sessions:[]
  $('nav-sessions-count').textContent=state.sessions.length
  renderList()
  if(!state.selectedSession&&state.sessions.length)await select(state.sessions[0].id)
  else if(state.selectedSession&&activeKey!==state.workspace+':'+state.selectedSession)await select(state.selectedSession)
  else if(state.selectedSession)await snapshot()
  else{
   empty($('chat-messages'),'Cada iniciativa tiene su conversación.','Abre una sesión para preparar trabajo, atender preguntas y consultar resultados.','chat',
    [button('Abrir una sesión',app.safe(()=>app.newSession()),'primary','plus')])
   updateComposer()
  }
 }
 $('session-search').addEventListener('input',()=>renderList(true))
 $('chat-input').addEventListener('input',()=>{saveDraft();updateComposer()})
 $('chat-input').addEventListener('keydown',event=>{
  if(event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();if(!$('send-button').disabled)$('chat-form').requestSubmit()}
 })
 $('chat-form').addEventListener('submit',app.safe(async event=>{
  event.preventDefault()
  if(!current||!['idle','interrupted'].includes(current.status))return
  const id=current.id,text=$('chat-input').value
  if(!text.trim())return
  if(!pendingSend||pendingSend.text!==text||pendingSend.id!==id)pendingSend={id,text,key:crypto.randomUUID().replaceAll('-','')}
  const request=pendingSend;$('send-button').disabled=true
  try{
   await app.api('sessions/'+id+'/messages',{method:'POST',body:{text,request_id:request.key}})
   if(state.selectedSession!==id)return
   if($('chat-input').value===text)$('chat-input').value=''
   saveDraft();pendingSend=null;await refresh()
  }catch(error){
   if(error instanceof app.Stale)return
   app.toast(app.explain(error),true);await refresh()
  }
 }))
 $('interrupt-button').addEventListener('click',app.safe(async()=>{
  if(!current)return
  await app.api('sessions/'+current.id+'/interrupt',{method:'POST',body:{}});await snapshot()
 }))
 $('resume-session').addEventListener('click',app.safe(async()=>{
  if(!current)return
  await app.api('sessions/'+current.id+'/resume',{method:'POST',body:{}});await refresh()
 }))
 $('disconnect-session').addEventListener('click',app.safe(async()=>{
  if(!current||!current.can_disconnect)return
  await app.api('sessions/'+current.id+'/disconnect',{method:'POST',body:{}});await refresh()
 }))
 $('chat-inspector-toggle').addEventListener('click',()=>{
  $('session-inspector').hidden=!$('session-inspector').hidden
  $('chat-inspector-toggle').setAttribute('aria-expanded',String(!$('session-inspector').hidden))
 })
 return {clear,refresh,select,draft,renderList}
}

