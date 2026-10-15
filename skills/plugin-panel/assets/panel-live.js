/* Read-only canonical ledger view; this asset is embedded only in served mode. */
(()=>{
 'use strict';
 const section=document.getElementById('operations');if(!section)return;
 const cards=document.getElementById('progress-cards'),status=document.getElementById('progress-status');
 const freshness=document.getElementById('progress-freshness'),results=document.getElementById('progress-results');
 const search=document.getElementById('progress-search'),state=document.getElementById('progress-state');
 const button=document.getElementById('progress-refresh');
 const states={'borrador':'Borrador','en-progreso':'En progreso','en-revision':'En revisión','completado':'Completado','cancelado':'Cancelado','unknown':'Sin estado reconocido'};
 let timer=null,inFlight=false,last=null,controller=null;
 const integer=value=>Number.isSafeInteger(value)&&value>=0;
 const text=value=>typeof value==='string'&&value.length<=320&&[...value].length<=160;
 function valid(data){
  if(!data||data.version!==1||data.source!=='canonical_ledger'||!['ok','partial','not_found','unavailable'].includes(data.status)||typeof data.complete!=='boolean')return false;
  if(typeof data.observed_at!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(data.observed_at)||!Number.isFinite(Date.parse(data.observed_at)))return false;
  if(!Array.isArray(data.initiatives)||data.initiatives.length>64||!Array.isArray(data.issues)||data.issues.length>16)return false;
  if(data.issues.some(issue=>!issue||typeof issue.status!=='string'||!/^[-a-z_]{1,48}$/.test(issue.status)))return false;
  const ids=new Set();
  for(const item of data.initiatives){
   if(!item||typeof item.id!=='string'||!/^[a-f0-9]{16}$/.test(item.id)||ids.has(item.id)||!text(item.title)||!Object.hasOwn(states,item.estado))return false;
   ids.add(item.id);
   if(!integer(item.total)||!integer(item.completadas)||item.completadas>item.total||!integer(item.pct)||item.pct>100)return false;
   if(typeof item.source_sha256!=='string'||!/^[a-f0-9]{64}$/.test(item.source_sha256))return false;
   if(item.fase!==null&&(!item.fase||!integer(item.fase.indice)||!integer(item.fase.total)||item.fase.indice<1||item.fase.indice>item.fase.total||!text(item.fase.nombre)))return false;
   if(!Array.isArray(item.en_progreso)||item.en_progreso.length>8||item.en_progreso.some(task=>!task||!text(task.id)||[...task.id].length>20||!text(task.titulo)))return false;
  }
  return true;
 }
 function element(tag,value,className){
  const node=document.createElement(tag);if(value!==undefined)node.textContent=value;if(className)node.className=className;return node;
 }
 function filter(){
  let visible=0;const query=search.value.toLocaleLowerCase();
  for(const card of cards.children){
   card.hidden=(state.value!=='all'&&card.dataset.state!==state.value)||!card.textContent.toLocaleLowerCase().includes(query);
   if(!card.hidden)visible++;
  }
  results.textContent=visible+' iniciativas visibles'+(last?.complete===false?' · lectura incompleta':'');
 }
 function render(data){
  const unchanged=last&&JSON.stringify(last.initiatives)===JSON.stringify(data.initiatives);
  const nodes=[];
  for(const item of unchanged?[]:data.initiatives){
   const card=element('article',undefined,'card progress-card');card.dataset.state=item.estado;
   card.append(element('small',states[item.estado]),element('h3',item.title||'Iniciativa sin título'));
   card.append(element('p',item.completadas+' de '+item.total+' tareas completadas · '+item.pct+' %'));
   if(item.fase)card.append(element('p','Fase '+item.fase.indice+' de '+item.fase.total+' · '+item.fase.nombre));
   if(item.en_progreso.length){
    card.append(element('p','Tareas declaradas en progreso'));
    const list=element('ul');for(const task of item.en_progreso)list.append(element('li',task.id+' · '+task.titulo));card.append(list);
   }
   const source=element('details');source.append(element('summary','Referencia de lectura'),element('code','SHA-256 del texto UTF-8: '+item.source_sha256));card.append(source);nodes.push(card);
  }
  if(!unchanged)cards.replaceChildren(...nodes);last=data;
  freshness.textContent='Lectura obtenida: '+data.observed_at+' · esta fecha no indica actividad de agentes.';
  if(data.status==='partial'||!data.complete)status.textContent='Lectura parcial: se muestran las iniciativas disponibles; los datos omitidos no acreditan ausencia ni un total completo.';
  else if(!data.initiatives.length)status.textContent='No se encontraron iniciativas con ledger en el proyecto seleccionado.';
  else status.textContent='Progreso derivado del ledger canónico. La lectura no acredita ejecución de agentes.';
  if(data.status==='not_found')status.textContent='No se encontró el roadmap del proyecto seleccionado; no hay ledger disponible.';
  filter();
 }
 function clearPoll(){if(timer!==null){clearTimeout(timer);timer=null;}}
 function schedule(){clearPoll();if(!document.hidden)timer=setTimeout(refresh,5000);}
 async function refresh(){
  clearPoll();if(document.hidden||inFlight)return;
  inFlight=true;button.disabled=true;controller=new AbortController();
  const requestController=controller;
  const deadline=setTimeout(()=>requestController.abort(),4000);
  try{
   const response=await fetch('api/progress',{credentials:'omit',cache:'no-store',signal:controller.signal});
   if(!response.ok)throw Error('unavailable');
   const data=await response.json();
   if(!valid(data)||data.status==='unavailable'||(data.status==='not_found'&&last))throw Error('unavailable');
   render(data);
  }catch{
   status.textContent=last?'No se pudo actualizar. Se conserva la última vista y su fecha anterior; no se acredita su vigencia.':'No se pudo actualizar el progreso. Sin lectura disponible; vuelve a intentarlo.';
  }finally{
   clearTimeout(deadline);controller=null;inFlight=false;button.disabled=false;schedule();
  }
 }
 search.addEventListener('input',filter);state.addEventListener('change',filter);button.addEventListener('click',refresh);
 document.addEventListener('visibilitychange',()=>{if(document.hidden){clearPoll();if(controller)controller.abort();}else refresh();});
 refresh();
})();
