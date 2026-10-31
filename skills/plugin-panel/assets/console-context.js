import {$,el,icon,button,badge,provider,providers,busy,relative,time,empty,loading,panel,progress,markdown} from './console-dom.js'

export function createContext(app){
 const state=app.state
 let overviewSignature='',activitySignature='',memorySignature='',integrationSignature='',catalogSignature='',catalogData=null,memoryResult=null
 function clear(){
  overviewSignature='';activitySignature='';memorySignature='';integrationSignature='';catalogSignature='';catalogData=null;memoryResult=null
  for(const id of ['overview-content','activity-content','memory-content','integrations-content','catalog-content'])$(id).replaceChildren()
  $('memory-search').value='';$('catalog-search').value=''
 }
 function metric(label,value,detail,symbol){
  const card=el('div',undefined,'metric-card'),header=el('div',label,'metric-label');header.append(icon(symbol))
  card.append(header,el('div',value??'—','metric-value'),el('small',detail));return card
 }
 async function overview(){
  const epoch=state.epoch
  const results=await Promise.allSettled([app.plans.portfolio(),app.api('sessions'),app.api('runtimes')])
  if(epoch!==state.epoch||state.view!=='overview')return
  const portfolio=results[0].status==='fulfilled'?results[0].value:null
  const sessions=results[1].status==='fulfilled'?results[1].value.sessions:null
  const runtimes=results[2].status==='fulfilled'?results[2].value.runtimes:[]
  if(sessions)state.sessions=sessions;if(runtimes)state.runtimes=runtimes
  $('nav-sessions-count').textContent=sessions?sessions.length:'—'
  if(portfolio?.freshness?.state==='refresh_failed')app.notice('La actualización de la cartera falló. Se conserva la lectura anterior con su fecha original.','warning')
  else if(results.some(r=>r.status==='rejected'))app.notice('Algunas fuentes no se han podido actualizar. Los datos ausentes se muestran sin cifra.','warning')
  else if(portfolio&&!portfolio.complete&&portfolio.status!=='not_found')app.notice('La cartera es parcial; se indican únicamente los datos observados.','warning')
  else app.notice('')
  const signature=JSON.stringify([portfolio?.iniciativas,portfolio?.totales,portfolio?.status,portfolio?.complete,
   portfolio?.freshness?.state==='refresh_failed',results.map(r=>r.status),sessions?.map(s=>[s.id,s.title,s.status]),runtimes])
  if(signature===overviewSignature)return;overviewSignature=signature
  const root=$('overview-content');root.replaceChildren()
  const rows=portfolio?.iniciativas||[],totals=portfolio?.totales?.tareas
  const measured=portfolio&&['ok','partial'].includes(portfolio.status)
  const prefix=portfolio&&!portfolio.complete?'≥ ':''
  const metrics=el('div',undefined,'metric-grid')
  metrics.append(metric('Planes con tareas',measured?prefix+rows.filter(r=>r.tareas).length:null,'Registro del proyecto','board'),
   metric('Tareas pendientes',totals?prefix+Math.max(0,totals.total-totals.completadas):null,totals?totals.total+' tareas observadas':'Sin registro medible','clock'),
   metric('Sesiones abiertas',sessions?sessions.filter(s=>busy.has(s.status)).length:null,'En esta consola · estado observado','chat'),
   metric('Entrega completada',totals?totals.pct+'%':null,totals?totals.completadas+' de '+totals.total+' tareas':'Sin datos de progreso','check'))
  root.append(metrics)
  const grid=el('div',undefined,'overview-grid'),left=el('div'),right=el('div')
  const work=panel('Continúa donde lo dejaste.','Conversaciones de este proyecto',button('Ver sesiones',app.safe(()=>app.navigate('sessions')),'quiet','arrow'))
  if(sessions?.length){
   for(const session of sessions.slice(0,4)){
    const row=el('div',undefined,'compact-row'),copy=el('div',undefined,'row-copy')
    copy.append(el('strong',session.title),el('small',(providers[session.runtime]||session.runtime)+' · '+relative(session.updated_at)))
    row.append(provider(session.runtime),copy,badge(session.status),button('Abrir',app.safe(()=>app.navigate('sessions',{session:session.id})),'quiet','arrow'));work.append(row)
   }
  }else{
   const start=el('div',undefined,'quick-start'),copy=el('div'),mark=el('div',undefined,'illustration-icon');mark.append(icon('chat'))
   copy.append(el('h3',sessions?'Tu equipo empieza con una conversación.':'Sesiones sin confirmar.'),
    el('p',sessions?'Concreta una idea, retoma un plan o pide una revisión. Elige el entorno que mejor encaje con el trabajo.':'Actualiza para comprobar las sesiones; no se interpreta una lectura fallida como una lista vacía.'))
   const actions=el('div',undefined,'quick-start-actions');actions.append(button('Abrir una sesión',app.safe(()=>app.newSession()),'primary','plus'),button('Preparar un plan',()=>app.openDialog('idea-dialog'),'secondary','board'));copy.append(actions);start.append(mark,copy);work.append(start)
  }
  const strip=el('div',undefined,'runtime-strip')
  for(const runtime of runtimes||[]){
   const chip=el('span',undefined,'runtime-chip')
   chip.append(provider(runtime.id),document.createTextNode((providers[runtime.id]||runtime.id)+' · '+(runtime.enabled&&runtime.installed?'detectado':runtime.enabled?'sin instalar':'no habilitado')))
   strip.append(chip)
  }
  if(!strip.childElementCount)strip.append(el('span','Entornos sin comprobar.','small-muted'))
  work.append(strip);left.append(work)
  const plans=panel('Planes del proyecto',measured?rows.length+' iniciativas observadas':'Preparando la cartera',button('Ver cartera',app.safe(()=>app.navigate('plans')),'quiet','arrow'))
  if(rows.length){
   for(const plan of rows.slice(0,5)){
    const row=el('div',undefined,'compact-row'),copy=el('div',undefined,'row-copy')
    const open=button(plan.titulo||plan.slug,app.safe(()=>app.navigate('plan',{plan:plan.id})),'quiet');open.className='plan-title-button'
    copy.append(open,el('small',plan.tareas?plan.tareas.completadas+' de '+plan.tareas.total+' tareas':'Por preparar'))
    const value=el('div',undefined,'compact-progress')
    if(plan.tareas)value.append(progress(plan.tareas.pct),el('small',plan.tareas.pct+'%'));else value.append(badge('borrador'))
    row.append(copy,value);plans.append(row)
   }
  }else{
   const container=el('div');empty(container,'Una idea puede convertirse en un plan.','Explica el objetivo y acuerda pasos que el equipo pueda comprobar.','board',[],true);plans.append(container)
  }
  right.append(plans);grid.append(left,right);root.append(grid)
 }
 function timeline(root,events){
  root.replaceChildren()
  for(const event of events.slice(0,50)){
   const item=el('div',undefined,'timeline-item'),mark=el('div',undefined,'timeline-mark'),copy=el('div',undefined,'timeline-copy')
   mark.append(icon(event.state==='failed'?'close':event.state==='started'?'clock':'check'))
   copy.append(el('strong',event.name||event.tool||'Operación'),el('small',(event.actor||event.role||'Rol no informado')+(event.session?' · '+event.session:'')))
   item.append(mark,copy,el('time',time(event.at??event.observed_at)));root.append(item)
  }
 }
 async function activity(){
  const epoch=state.epoch
  const [history,sessions]=await Promise.all([app.api('activity'),app.api('sessions')])
  if(epoch!==state.epoch||state.view!=='activity')return
  state.sessions=sessions.sessions||[]
  const connected=state.sessions.filter(s=>!['disconnected','failed'].includes(s.status)).slice(0,8)
  const snapshots=await Promise.allSettled(connected.map(s=>app.api('sessions/'+s.id)))
  if(epoch!==state.epoch||state.view!=='activity')return
  const live=snapshots.filter(r=>r.status==='fulfilled').map(r=>r.value)
  const events=live.flatMap(s=>(s.events||[]).map(e=>({...e,session:s.title})))
  const old=history.recientes||[]
  events.push(...old.map(e=>({...e,name:e.tool,actor:e.role,at:e.observed_at,session:'Captura de hooks'})))
  const stamp=value=>new Date(typeof value==='number'&&value<1e12?value*1000:value).getTime()
  events.sort((a,b)=>stamp(b.at)-stamp(a.at))
  const failed=snapshots.filter(r=>r.status==='rejected').length
  const bounded=live.some(s=>s.truncated)
  const warnings=[]
  if(history.status==='unavailable'&&history.reason!=='disabled')warnings.push('El historial de actividad no está disponible; revisa su captura y diagnóstico.')
  else if(history.status==='partial')warnings.push('El historial de actividad es parcial.')
  if(failed)warnings.push('No se pudo leer la actividad de '+failed+' conexión'+(failed===1?'':'es')+'; su estado no se interpreta como vacío.')
  if(warnings.length)app.notice(warnings.join(' '),'warning')
  else if(history.reason==='disabled')app.notice('La captura de hooks está desactivada. Se muestran únicamente las señales recibidas de las conexiones disponibles.')
  else if(bounded||history.collection_complete===false)app.notice('Ventana de actividad acotada; no representa todo el historial ni todas las operaciones.')
  else app.notice('')
  const signature=JSON.stringify([live.map(s=>[s.id,s.status,s.events]),history.runs,history.recientes,
   history.status,history.reason,history.collection_complete,failed,bounded])
  if(signature===activitySignature)return;activitySignature=signature
  const root=$('activity-content');root.replaceChildren()
  const stage=el('div',undefined,'agent-stage'),head=el('div',undefined,'agent-stage-title')
  head.append(el('h2','El trabajo, con su contexto.'),el('span','Observación · sin razonamiento interno','small-muted'));stage.append(head)
  const nodes=el('div',undefined,'agent-nodes')
  for(const session of live){
   const node=el('article',undefined,'agent-node'+(busy.has(session.status)?' observed-active':''))
   node.append(provider(session.runtime),el('h3',session.title),el('p',providers[session.runtime]+' · sesión de esta consola'),badge(session.status))
   node.append(button('Abrir conversación',app.safe(()=>app.navigate('sessions',{session:session.id})),'quiet','arrow'));nodes.append(node)
  }
  for(const run of (history.runs||[]).slice(0,12)){
   const node=el('article',undefined,'agent-node'),avatar=el('span',(run.role||'SE').slice(0,2).toUpperCase(),'agent-avatar')
   node.append(avatar,el('h3',run.role||'Sesión sin rol informado'),el('p',(run.runtime||'Entorno')+' · captura de hooks'),
    badge(run.estado==='en_curso'?'running':'disconnected',run.estado==='en_curso'?'Señal reciente':'Sin señal reciente'))
   if(run.ultima_herramienta)node.append(el('p','Última operación: '+run.ultima_herramienta,'small-muted'));nodes.append(node)
  }
  if(!nodes.childElementCount)empty(nodes,'La actividad aparecerá aquí.','Abre una sesión para observar sus operaciones. La captura de hooks es una opción adicional del proyecto.','activity',
   [button('Abrir sesión',app.safe(()=>app.newSession()),'primary','plus')])
  stage.append(nodes);root.append(stage)
  const feed=panel('Línea de actividad','Operaciones informadas por las conexiones y la captura local')
  const body=el('div',undefined,'activity-feed')
  if(events.length)timeline(body,events);else empty(body,'Todavía no hay operaciones.','Una señal ausente no demuestra que todo esté parado. Solo se muestran operaciones recibidas.','clock',[],true)
  feed.append(body);feed.style.marginTop='20px';root.append(feed)
  root.append(el('p','Las conexiones pueden omitir subagentes, skills o herramientas. La actividad es informativa y puede tener huecos; el estado del plan se consulta por separado.','native-limits'))
 }
 async function memory(){
  const value=await app.api('memory')
  if(state.view!=='memory')return
  memoryResult=value;const signature=JSON.stringify([value.entradas,value.bandeja,value.backends,value.status,value.freshness?.state==='refresh_failed'])
  if(signature===memorySignature)return;memorySignature=signature;renderMemory(value)
 }
 function entry(row,query=false){
  const item=el('article',undefined,'knowledge-item'),mark=el('div',undefined,'illustration-icon'),copy=el('div')
  mark.append(icon('file'));copy.append(el('h3',row.titular||row.id||'Entrada de conocimiento'))
  const text=row.resumen||row.texto||row.evidencia
  if(text)copy.append(el('p',String(text).slice(0,450)))
  const meta=el('div',undefined,'knowledge-meta')
  meta.append(el('span',row.tipo||row.category||'Conocimiento'),el('span',row.estado||'Sin estado'),el('span',row.version?'Versión '+row.version:'Versión sin datos'))
  copy.append(meta)
  if(row.id)copy.append(button('Leer la entrada',app.safe(async()=>{
   const result=await app.api('memory/query',{method:'POST',body:{operation:'show',id:row.id,limit:10}})
   const selected=result.selected
   const source=selected||result.entries?.[0]
   const box=el('div',undefined,'document-view')
   box.append(el('h2',source?.titular||row.id),el('p',source?.ruta||row.ruta||'Fuente local','small-muted'),
    markdown(source?.texto||source?.cuerpo||'La entrada no se pudo recuperar de forma completa.'),
    button('Volver a memoria',()=>{memorySignature='';app.safe(memory)()},'quiet','arrow'))
   $('memory-content').replaceChildren(box)
  }),'quiet','arrow'))
  item.append(mark,copy);return item
 }
 function renderMemory(value){
  const root=$('memory-content'),grid=el('div',undefined,'memory-grid')
  if(value.status==='calculating'){loading(root,'Leyendo la memoria local del proyecto…');return}
  const corpus=panel('Memoria local','Fuentes del proyecto, separadas por estado')
  const rows=value.entradas||[]
  if(rows.length)for(const row of rows)corpus.append(entry(row))
  else{
   const body=el('div');empty(body,'Lo que vale la pena recordar.','Cuando haya decisiones o aprendizajes guardados, podrás consultarlos aquí con sus fuentes.','memory',
    [button('Preparar una propuesta',app.safe(()=>app.newSession('Propuesta de memoria','Ayúdame a proponer conocimiento reutilizable del proyecto con evidencia. Usa el proceso de knowledge-curator; no lo apruebes ni publiques por tu cuenta.')),'secondary')]);corpus.append(body)
  }
  const explanation=panel('Cada cosa en su lugar.','La memoria local funciona sin servicios externos'),body=el('div',undefined,'memory-explanation')
  for(const [title,text] of [['Aprobado','Decisiones, reglas y aprendizajes que han pasado el proceso de curación.'],
   ['Propuestas','Candidatos pendientes de revisión. No se convierten en reglas por aparecer en esta vista.'],
   ['Journal','Continuidad de sesiones. Describe lo ocurrido y conserva pendientes; no es conocimiento aprobado.'],
   ['Kwipu, Graphiti y Graphify','Integraciones opcionales con funciones diferentes. Configurar una no demuestra que esté conectada ni que su respuesta sea correcta.']]){
   body.append(el('h3',title),el('p',text))
  }
  body.append(button('Ver integraciones',app.safe(()=>app.navigate('integrations')),'quiet','plug'))
  explanation.append(body);grid.append(corpus,explanation);root.replaceChildren(grid)
  if(value.status!=='ok')root.prepend(el('p','La vista puede ser parcial o no estar disponible. Consulta los estados antes de interpretar una ausencia.','notice warning'))
  if(value.freshness?.state==='refresh_failed')root.prepend(el('p','La actualización falló. Esta es la última lectura disponible, con su fecha original.','notice warning'))
 }
 $('memory-search-form').addEventListener('submit',app.safe(async event=>{
  event.preventDefault();const text=$('memory-search').value.trim()
  if(!text){memorySignature='';await memory();return}
  const result=await app.api('memory/query',{method:'POST',body:{operation:'search',text,limit:10}})
  const root=$('memory-content'),box=panel('Resultados locales','La búsqueda no activa servicios externos')
  if(result.entries?.length)for(const row of result.entries)box.append(entry(row,true))
  else{const body=el('div');empty(body,'No hay resultados en esta consulta.','Refina los términos y comprueba las fuentes; una ausencia no demuestra que no exista conocimiento.','search',[],true);box.append(body)}
  root.replaceChildren(box)
 }))
 async function integrations(){
  const [data,runtimeData]=await Promise.all([app.api('integrations'),app.api('runtimes')])
  if(state.view!=='integrations')return
  state.runtimes=runtimeData.runtimes||[]
  const invalidRoute=data.integrations&&!['declared','absent','no_match','disabled'].includes(data.integrations.status)
  const invalidMemory=(data.memory_services||[]).some(row=>row.status==='invalid_configuration')
  if(invalidRoute||invalidMemory)app.notice('No se ha podido leer toda la configuración de integraciones. Revisa los archivos del proyecto; la ausencia de filas no demuestra que no haya integraciones.','warning')
  else app.notice('')
  const signature=JSON.stringify([data,runtimeData]);if(signature===integrationSignature)return;integrationSignature=signature
  const root=$('integrations-content');root.replaceChildren()
  const runtimeGrid=el('div',undefined,'integration-grid')
  for(const runtime of state.runtimes){
   const card=el('article',undefined,'integration-card'),top=el('div',undefined,'integration-card-top')
   top.append(provider(runtime.id),badge(runtime.enabled&&runtime.installed?'idle':'disconnected',runtime.enabled&&runtime.installed?'Ejecutable detectado':runtime.enabled?'Sin instalar':'No habilitado'))
   card.append(top,el('h3',providers[runtime.id]||runtime.id),el('p','Sesiones y chat mediante la interfaz nativa. Conserva su configuración y permisos.'))
   const open=button('Abrir sesión',app.safe(()=>app.newSession('','',runtime.id)),'secondary','chat');open.disabled=!runtime.enabled||!runtime.installed;card.append(open)
   card.append(el('p','La detección no acredita conexión. No se controlan ventanas Desktop ni se presupone paridad de funciones.','native-limits'));runtimeGrid.append(card)
  }
  root.append(el('h2','Entornos de trabajo'),runtimeGrid)
  const heading=el('div',undefined,'section-heading');heading.append(el('h2','Integraciones de este proyecto'),
   button('Preparar integración',app.safe(()=>app.newSession('Preparar integración','Ayúdame a configurar una integración opcional de este proyecto mediante el puerto común. Concreta necesidad, permisos y destino; presenta una propuesta y pruebas antes de publicar nada.')),'secondary','plus'));root.append(heading)
  const grid=el('div',undefined,'integration-grid'),bindings=data.integrations?.bindings||[]
  for(const binding of bindings){
   const card=el('article',undefined,'integration-card')
   card.append(badge('uncertain','Declarada · conexión sin comprobar'),el('h3',binding.id),el('p',binding.purpose+' · '+binding.adapter?.name))
   const pills=el('div',undefined,'pill-list');for(const operation of binding.capabilities||[])pills.append(el('span',operation,'pill'));card.append(pills)
   card.append(el('p','Las escrituras conservan autorización, vista previa y recibos. Esta vista no ejecuta comprobaciones de red.','native-limits'));grid.append(card)
  }
  for(const backend of data.memory_services||[]){
   if(!backend.id)continue
   const card=el('article',undefined,'integration-card')
   card.append(badge(backend.enabled?'uncertain':'disconnected',backend.enabled?'Configurada · sin comprobar':'Desactivada'),
    el('h3',backend.id),el('p','Servicio opcional de memoria · '+backend.type+(backend.mode?' · '+backend.mode:'')),
    el('p','Aprobar memoria y publicarla son operaciones separadas. La lectura externa requiere su propia autorización.','small-muted'));grid.append(card)
  }
  if(!grid.childElementCount)empty(grid,'Elige las herramientas que os ayudan.','Puedes conectar seguimiento, documentación o memoria desde la configuración del proyecto. El core funciona sin ellas.','plug',[],true)
  root.append(grid,el('p','El proyecto puede usar otros proveedores: una integración propia no necesita añadirse al catálogo del core. Graphify es un extractor de contexto de código opcional, distinto de Kwipu y Graphiti.','native-limits'))
 }
 function renderCatalog(){
  const root=$('catalog-content'),query=$('catalog-search').value.trim().toLowerCase(),grid=el('div',undefined,'catalog-grid')
  const labels={agent:'Agente',skill:'Skill',command:'Comando',persona:'Persona de dominio',mcp:'MCP declarado','tool-source':'Fuente de herramientas',tool:'Herramienta declarada',hook:'Hook declarado'}
  const pieces=[]
  for(const [kind,singular] of [['agents','agent'],['skills','skill'],['commands','command']]){
   pieces.push(...(catalogData?.[kind]||[]).map(piece=>({...piece,kind:singular,scope:'bundle'})))
  }
  pieces.push(...(catalogData?.extensions?.pieces||[]))
  pieces.push(...(catalogData?.tools||[]).map(name=>({name,kind:'tool',scope:'bundle',description:'Declarada por agentes del bundle; disponibilidad de sesión sin comprobar.'})))
  pieces.push(...(catalogData?.hooks||[]).map(row=>({name:row.handler||row.event,kind:'hook',scope:'bundle',runtime:row.runtime,source:row.source,
   description:(row.event||'Evento')+' · '+(row.function||row.description||'Ejecución sin comprobar.')})))
  for(const piece of pieces){
    const name=piece.name||piece.id||piece.title||'Pieza',description=piece.description||piece.summary||''
    if(!(name+' '+description+' '+piece.kind+' '+piece.scope+' '+(piece.runtime||'')).toLowerCase().includes(query))continue
    const card=el('article',undefined,'integration-card')
    card.append(badge('disconnected',labels[piece.kind]||piece.kind),el('h3',name),el('p',description))
    card.append(el('p',(piece.scope==='bundle'?'Bundle':'Proyecto')+(piece.runtime?' · '+(providers[piece.runtime]||piece.runtime):'')+(piece.source?' · '+piece.source:''),'small-muted'))
    if(piece.kind==='skill')card.append(button('Preparar uso en una sesión',app.safe(()=>app.newSession('Usar '+String(name).slice(0,85),'Quiero utilizar la skill '+name+' en este proyecto. Revisa primero su disponibilidad, alcance, origen y posibles conflictos antes de invocarla.')),'quiet','arrow'))
    grid.append(card)
  }
  if(!grid.childElementCount)empty(root,'Sin piezas con ese filtro.','Prueba otro término o revisa la instalación.','search')
  else root.replaceChildren(grid)
 }
 async function catalog(){
  if(!catalogData)loading($('catalog-content'),'Leyendo las capacidades del proyecto…')
  const value=await app.api('catalog')
  if(state.view!=='catalog')return
  if(value.status==='calculating'){loading($('catalog-content'),'Leyendo las capacidades del proyecto…');return}
  catalogData=value
  const signature=JSON.stringify([value.agents,value.skills,value.commands,value.tools,value.hooks,value.extensions])
  if(signature!==catalogSignature){catalogSignature=signature;renderCatalog()}
  const conflicts=value.extensions?.conflicts?.length||0
  if(value.status==='unavailable')app.notice('No se ha podido leer el inventario. Actualiza o revisa la instalación.','warning')
  else if(value.freshness?.state==='refresh_failed')app.notice('La actualización del catálogo falló. Se muestra la última lectura disponible.','warning')
  else if(conflicts||value.extensions?.partial)app.notice('Inventario parcial o con conflictos de nombres. Contrasta el origen y la disponibilidad antes de usar una pieza.','warning')
  else app.notice('Inventario de declaraciones. Una pieza encontrada no acredita que el entorno la haya cargado ni que tenga permiso para ejecutarla.')
 }
 $('catalog-search').addEventListener('input',renderCatalog)
 return {clear,overview,activity,memory,integrations,catalog}
}

