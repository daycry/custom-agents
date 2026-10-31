import {$,el,icon,button,badge,relative,empty,loading,panel,progress,markdown,key} from './console-dom.js'

export function createPlans(app){
 const state=app.state
 let mode='list',detailData=null,detailSignature='',detailTab='board',phase='all',taskSequence=0,taskContext=null,commentRequest=null
 const drafts=new Map()
 const group=row=>row.tareas&&row.tareas.total>0?(row.tareas.completadas===row.tareas.total?'done':'active'):'draft'
 function clear(){detailData=null;detailSignature='';detailTab='board';phase='all';taskSequence++;taskContext=null;commentRequest=null;$('plan-detail').replaceChildren();$('plans-content').replaceChildren();$('task-content').replaceChildren();$('task-comments').replaceChildren();$('comment-input').value='';$('comment-submit').disabled=true}
 async function portfolio(){
  const data=await app.api('plans');state.portfolio=data;app.observed(data.observed_at);return data
 }
 function card(row){
  const node=el('article',undefined,'plan-card'),top=el('div',undefined,'plan-card-top')
  const status=group(row),statusNode=badge(status==='done'?'completado':status==='active'?'en-progreso':'borrador',status==='active'?'Trabajo pendiente':undefined)
  top.append(statusNode,el('span',row.fecha||'Sin fecha','date'))
  const title=button(row.titulo||row.slug,app.safe(()=>app.navigate('plan',{plan:row.id})),'quiet');title.className='plan-title-button'
  node.append(top,title,el('p',row.tareas?row.tareas.total+' tareas · '+row.tareas.completadas+' completadas':'Sin registro de tareas disponible'))
  if(row.tareas)node.append(progress(row.tareas.pct))
  const bottom=el('div',undefined,'plan-card-bottom')
  bottom.append(el('span',row.tareas?row.tareas.pct+'% del registro':'Por preparar'),button('Abrir plan',app.safe(()=>app.navigate('plan',{plan:row.id})),'quiet','arrow'))
  node.append(bottom);return node
 }
 function render(){
  const root=$('plans-content'),query=$('plan-search').value.trim().toLowerCase(),filter=$('plan-filter').value
  const all=state.portfolio?.iniciativas||[]
  const rows=all.filter(row=>(row.titulo||row.slug||'').toLowerCase().includes(query)&&(filter==='all'||group(row)===filter))
  if(!rows.length){
   empty(root,all.length?'No hay planes con ese filtro.':'Tu próxima entrega empieza aquí.',
    all.length?'Cambia el texto o el estado para ver otros planes.':'Describe una necesidad y prepara un plan con pasos y criterios que puedas revisar.','board',
    all.length?[button('Limpiar filtros',()=>{$('plan-search').value='';$('plan-filter').value='all';render()},'secondary')]:
     [button('Crear un plan',()=>app.openDialog('idea-dialog'),'primary','plus')]);return
  }
  root.replaceChildren()
  if(mode==='board'){
   const board=el('div',undefined,'kanban');board.setAttribute('aria-label','Cartera por situación de trabajo')
   for(const [id,title] of [['draft','Por preparar'],['active','Trabajo pendiente'],['done','Completados']]){
    const column=el('section',undefined,'kanban-column'),heading=el('h3',title),items=rows.filter(r=>group(r)===id)
    heading.append(el('span',items.length,'column-count'));column.append(heading)
    for(const row of items)column.append(card(row))
    if(!items.length)column.append(el('p','Sin planes en esta columna.','column-empty'));board.append(column)
   }
   root.append(board)
  }else{const grid=el('div',undefined,'plan-grid');for(const row of rows)grid.append(card(row));root.append(grid)}
 }
 async function load(){
  const data=await portfolio()
  if(state.view!=='plans')return
  if(data.status==='calculating'){loading($('plans-content'));return}
  if(data.freshness?.state==='refresh_failed')app.notice('La actualización de la cartera falló. Se conserva la lectura anterior con su fecha original.','warning')
  else if(!data.complete&&data.status!=='not_found')app.notice('La cartera es parcial. Algunas fuentes no se han podido leer; sus datos no cuentan como cero.','warning')
  else app.notice('')
  render()
 }
 function board(){
  const root=el('div'),toolbar=el('div',undefined,'toolbar'),label=el('label','Fase: ','phase-filter'),select=el('select')
  select.setAttribute('aria-label','Filtrar tareas por fase')
  const phases=[...new Set((detailData.tareas||[]).map(t=>t.fase_nombre).filter(Boolean))]
  for(const value of ['all',...phases]){const option=el('option',value==='all'?'Todas las fases':value);option.value=value;select.append(option)}
  select.value=phases.includes(phase)?phase:'all';phase=select.value
  select.addEventListener('change',()=>{phase=select.value;renderDetail()})
  label.append(select);toolbar.append(label,el('span','Los estados reflejan el registro del plan.','small-muted'));root.append(toolbar)
  const rows=(detailData.tareas||[]).filter(t=>phase==='all'||t.fase_nombre===phase)
  const columns=[['borrador','Por hacer',''],['en-progreso','En marcha','active'],['en-revision','En revisión','review'],['completado','Completadas','done'],['cancelado','Canceladas','']]
  if(rows.some(t=>!columns.some(c=>c[0]===t.estado_tarea)))columns.push(['unknown','Por aclarar',''])
  const kanban=el('div',undefined,'kanban');kanban.setAttribute('aria-label','Tareas por estado')
  for(const [value,title,dot] of columns){
   const column=el('section',undefined,'kanban-column'),heading=el('h3')
   const items=rows.filter(t=>value==='unknown'?!columns.some(c=>c[0]===t.estado_tarea):t.estado_tarea===value)
   heading.append(el('span',undefined,'column-dot '+dot),document.createTextNode(title),el('span',items.length,'column-count'));column.append(heading)
   for(const task of items){
    const node=el('button',undefined,'task-card');node.type='button';node.dataset.task=task.id
    node.append(el('small',task.id+' · '+(task.fase_nombre||'Sin fase')),el('strong',task.titulo))
    const footer=el('span',undefined,'task-card-footer')
    footer.append(el('span',task.gaps?task.gaps+' hallazgos pendientes':'Ver detalle'),icon('arrow'));node.append(footer)
    node.addEventListener('click',app.safe(()=>openTask(task.id)));column.append(node)
   }
   if(!items.length)column.append(el('p','Sin tareas en este estado.','column-empty'));kanban.append(column)
  }
  root.append(kanban);return root
 }
 function renderDetail(){
  const root=$('plan-detail'),row=state.portfolio?.iniciativas?.find(r=>r.id===state.plan)
  const title=row?.titulo||detailData.slug||'Plan del proyecto'
  $('view-title').textContent=title
  const summary=el('div',undefined,'plan-summary'),copy=el('div')
  copy.append(el('h2','Progreso de la entrega'),el('p',(detailData.tareas?.length??0)+' tareas en el registro · abre una tarjeta para consultar sus criterios, revisión y notas.'))
  const controls=el('div',undefined,'plan-summary-right')
  const tasks=detailData.tareas||[],done=tasks.filter(t=>t.estado_tarea==='completado').length
  controls.append(el('span',tasks.length?Math.round(done*100/tasks.length)+'%':'—','metric-value'),
   button('Continuar en una sesión',app.safe(()=>app.run(state.plan)),'primary','arrow'))
  summary.append(copy,controls)
  const tabs=el('nav',undefined,'detail-tabs');tabs.setAttribute('aria-label','Contenido del plan')
  for(const [id,label] of [['board','Tareas y fases'],['plan','Plan de trabajo'],['spec','Objetivo y requisitos'],['evaluation','Evaluación'],['design','Diseño']]){
   const tab=button(label,app.safe(async()=>{detailTab=id;renderDetail();if(id!=='board')await documentView(id)}),'quiet')
   tab.setAttribute('aria-pressed',String(detailTab===id));tabs.append(tab)
  }
  const body=el('div');body.id='plan-detail-body'
  root.replaceChildren(summary,tabs,body)
  if(detailTab==='board')body.append(board())
  else loading(body,'Leyendo el documento…')
  if(!detailData.complete)root.prepend(el('p','Vista parcial del registro. Revisa las advertencias antes de aceptar una entrega.','notice warning'))
 }
 async function documentView(kind){
  const selected=state.plan
  try{
   const value=await app.api('plans/'+selected+'/documents/'+kind)
   if(selected!==state.plan||detailTab!==kind||state.view!=='plan')return
   const box=el('div',undefined,'document-view')
   box.append(el('p','Documento consultado ahora · '+value.source,'small-muted'),markdown(value.text))
   if(value.truncated)box.append(el('p','El documento se ha recortado en esta vista.','notice warning'))
   box.append(button('Volver a leer el documento',app.safe(()=>documentView(kind)),'quiet','refresh'))
   $('plan-detail-body').replaceChildren(box)
  }catch(error){
   if(error instanceof app.Stale)return
   if(selected===state.plan&&detailTab===kind)empty($('plan-detail-body'),'Documento no disponible.',app.explain(error),'file',
    [button('Volver a tareas',()=>{detailTab='board';renderDetail()},'secondary')])
  }
 }
 async function detail(){
  if(!state.plan)return
  const selected=state.plan,value=await app.api('plans/'+selected)
  if(state.view!=='plan'||selected!==state.plan)return
  app.observed(value.observed_at)
  if(!Array.isArray(value.tareas)){empty($('plan-detail'),'Este registro no se puede mostrar.','Revisa el plan o solicita un diagnóstico desde una sesión.','board');return}
  const signature=JSON.stringify([value.tareas,value.status,value.complete,selected])
  detailData=value
  if(signature===detailSignature)return
  detailSignature=signature;renderDetail();if(detailTab!=='board')await documentView(detailTab)
 }
 function renderComments(value){
  if(!taskContext)return
  taskContext.revision=value.revision
  const root=$('task-comments');root.replaceChildren()
  for(const note of value.comments||[]){
   const node=el('article',undefined,'comment'),header=el('header')
   header.append(el('span',note.actor),el('time',timeLabel(note.created_at)));node.append(header,el('p',note.text));root.append(node)
  }
  if(!value.comments?.length)root.append(el('p','Todavía no hay notas para esta tarea.','small-muted'))
 }
 function timeLabel(value){return new Date(value).toLocaleString('es',{dateStyle:'short',timeStyle:'short'})}
 async function openTask(id){
  const serial=++taskSequence,plan=state.plan,workspace=state.workspace
  taskContext={id,plan,workspace,revision:0,ready:false};commentRequest=null
  $('comment-submit').disabled=true
  $('task-id').textContent=id;$('task-title').textContent='Leyendo la tarea…';$('comment-error').textContent=''
  $('comment-input').value=drafts.get(workspace+':'+plan+':'+id)||''
  loading($('task-content'));$('task-comments').replaceChildren();app.openDialog('task-dialog')
  const [value,comments]=await Promise.all([app.api('plans/'+plan+'/tasks/'+id),app.api('plans/'+plan+'/tasks/'+id+'/comments')])
  if(serial!==taskSequence||state.plan!==plan||workspace!==state.workspace)return
  const task=value.tarea;$('task-title').textContent=task.titulo
  const root=$('task-content');root.replaceChildren(badge(task.estado_tarea),el('p',task.descripcion||'Sin descripción registrada.','task-description'))
  if(!value.complete)root.append(el('p','El detalle es parcial. Algunos criterios o hallazgos pueden quedar fuera de esta vista.','notice warning'))
  if(task.criterios?.length){
   root.append(el('h3','Cómo se acepta esta tarea'))
   const list=el('ul',undefined,'criteria-list')
   for(const criterion of task.criterios){const item=el('li');item.append(icon(criterion.marcado?'check':'clock'),el('span',criterion.criterio));list.append(item)}
   root.append(list)
  }
  root.append(el('h3','Verificación registrada'),el('p',task.verificacion||'No hay instrucciones de verificación registradas.','task-description'))
  if(task.ejecutada)root.append(el('p','Ejecutada: '+task.ejecutada,'small-muted'))
  if(task.salida)root.append(markdown(task.salida))
  if(task.revision)root.append(el('p','Revisión · intento '+task.revision.intento+' · '+task.revision.abiertos+' hallazgos abiertos.','small-muted'))
  for(const gap of task.gaps||[])root.append(el('p',gap.grado+': '+gap.gap,'gap-item'))
  const actions=el('div',undefined,'integration-actions')
  actions.append(button('Trabajar en esta tarea',app.safe(async()=>{app.closeDialog('task-dialog');await app.run(plan,'continue',id)}),'secondary','arrow'),
   button('Solicitar revisión',app.safe(async()=>{app.closeDialog('task-dialog');await app.run(plan,'review',id)}),'secondary','check'))
  root.append(actions);renderComments(comments);taskContext.ready=true;$('comment-submit').disabled=false
 }
 $('comment-input').addEventListener('input',()=>{if(taskContext)drafts.set(taskContext.workspace+':'+taskContext.plan+':'+taskContext.id,$('comment-input').value)})
 $('comment-form').addEventListener('submit',app.safe(async event=>{
  event.preventDefault();const context=taskContext;if(!context?.ready)return
  const text=$('comment-input').value.trim();if(!text)return
  if(!commentRequest||commentRequest.text!==text)commentRequest={key:key(),text}
  const request=commentRequest,path='plans/'+context.plan+'/tasks/'+context.id+'/comments'
  $('comment-submit').disabled=true;$('comment-error').textContent=''
  try{
   await app.api(path,{method:'POST',body:{text,expected_revision:context.revision,request_id:request.key}})
   if(context!==taskContext)return
   $('comment-input').value='';drafts.delete(context.workspace+':'+context.plan+':'+context.id);commentRequest=null
   const comments=await app.api(path)
   if(context!==taskContext)return
   renderComments(comments);app.toast('Nota guardada en esta tarea.')
  }catch(error){
   if(error instanceof app.Stale)return
   if(context===taskContext){
    $('comment-error').textContent=app.explain(error)
    try{const comments=await app.api(path);if(context===taskContext)renderComments(comments)}catch{}
   }
  }finally{if(context===taskContext)$('comment-submit').disabled=!context.ready}
 }))
 $('plan-search').addEventListener('input',render);$('plan-filter').addEventListener('change',render)
 $('plans-list-toggle').addEventListener('click',()=>{mode='list';$('plans-list-toggle').setAttribute('aria-pressed','true');$('plans-board-toggle').setAttribute('aria-pressed','false');render()})
 $('plans-board-toggle').addEventListener('click',()=>{mode='board';$('plans-list-toggle').setAttribute('aria-pressed','false');$('plans-board-toggle').setAttribute('aria-pressed','true');render()})
 return {clear,load,portfolio,render,detail,card,openTask}
}

