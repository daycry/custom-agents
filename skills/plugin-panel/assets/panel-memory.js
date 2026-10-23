/* Explicit local knowledge queries; embedded only in the served panel. */
(()=>{
 'use strict';
 const section=document.getElementById('memory-query');if(!section)return;
 const form=document.getElementById('memory-form'),search=document.getElementById('memory-search');
 const text=document.getElementById('memory-text'),area=document.getElementById('memory-area'),type=document.getElementById('memory-type');
 const status=document.getElementById('memory-status'),freshness=document.getElementById('memory-freshness');
 const results=document.getElementById('memory-results'),resultsDate=document.getElementById('memory-results-date');
 const selected=document.getElementById('memory-selected'),relations=document.getElementById('memory-related');
 const statuses=['ok','partial','not_found','unavailable','ambiguous','invalid_request'];
 const groups={sucesion:'Sucesión',iniciativa:'Iniciativa compartida',area:'Área compartida',enlaces:'Enlaces declarados'};
 const controls=/[\x00-\x1f\x7f-\x9f\u2028\u2029\u202a-\u202e\u2066-\u2069]/;
 let busy=false,last=null;const actionButtons={results:new Set(),selected:new Set(),related:new Set()};
 const integer=value=>Number.isSafeInteger(value)&&value>=0;
 const string=(value,max)=>typeof value==='string'&&value.length<=max*2&&[...value].length<=max;
 const knowledgeVersion=value=>value===null||(integer(value)&&value>0)||
  (string(value,4300)&&/^[1-9][0-9]*$/.test(value));
 const identifier=value=>string(value,256)&&value.length>0&&!controls.test(value);
 const relative=value=>string(value,1000)&&value.length>0&&!/^[\/\\]|:/.test(value)&&!value.split(/[\/\\]/).includes('..');
 function compact(entry){
  return entry&&identifier(entry.id)&&['tipo','estado','estado_detalle','titular','area'].every(key=>string(entry[key],160))&&
   knowledgeVersion(entry.version)&&(entry.category===null||string(entry.category,160))&&
   string(entry.evidencia,1000)&&relative(entry.ruta)&&['legacy','approved'].includes(entry.origen)&&
   typeof entry.source_sha256==='string'&&/^[a-f0-9]{64}$/.test(entry.source_sha256);
 }
 function valid(data,request){
  if(!data||data.version!==1||data.source!=='canonical_knowledge'||data.operation!==request.operation||
     !statuses.includes(data.status)||typeof data.complete!=='boolean')return false;
  if(!string(data.observed_at,40)||!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(data.observed_at)||!Number.isFinite(Date.parse(data.observed_at)))return false;
  if(!Array.isArray(data.issues)||data.issues.some(code=>!string(code,64)||!/^[-a-z_]+$/.test(code)))return false;
  if(!data.budget||!integer(data.budget.files)||data.budget.files>128||!integer(data.budget.bytes)||data.budget.bytes>2097152||!integer(data.budget.entries)||data.budget.entries>256)return false;
  if(Object.hasOwn(data.budget,'scans')&&(!integer(data.budget.scans)||data.budget.scans>256))return false;
  if(!Array.isArray(data.entries)||data.entries.length>20||data.entries.some(entry=>!compact(entry)||Object.hasOwn(entry,'texto')))return false;
  if(['ok','not_found'].includes(data.status)&&!data.complete)return false;
  if(['partial','ambiguous','unavailable','invalid_request'].includes(data.status)&&data.complete)return false;
  if(['ambiguous','not_found','unavailable','invalid_request'].includes(data.status)&&
     (data.entries.length||data.selected!==null||data.related!==null))return false;
  if(new TextEncoder().encode(JSON.stringify(data)).length>65536)return false;
  if(request.operation==='search')return data.selected===null&&data.related===null;
  if(data.entries.length)return false;
  if(request.operation==='show')return data.related===null&&(data.selected===null||
   (compact(data.selected)&&data.selected.id===request.id&&string(data.selected.texto,12000)));
  if(data.selected!==null)return false;
  if(data.related===null)return true;
  let count=0;
  for(const group of Object.keys(groups)){
   const rows=data.related[group];if(!Array.isArray(rows))return false;count+=rows.length;
   for(const row of rows){
    if(group==='sucesion'){
     if(!row||!string(row.relation,160)||!identifier(row.id)||
        (row.entry!==null&&(!compact(row.entry)||row.entry.id!==row.id||Object.hasOwn(row.entry,'texto'))))return false;
    }else if(!compact(row)||Object.hasOwn(row,'texto'))return false;
   }
  }
  return count<=20;
 }
 function element(tag,value,className){
  const node=document.createElement(tag);if(value!==undefined)node.textContent=value;if(className)node.className=className;return node;
 }
 function action(label,operation,id,bucket){
  const button=element('button',label);button.type='button';button.disabled=busy;
  button.addEventListener('click',()=>query({operation,id}));bucket.add(button);return button;
 }
 function card(entry,bucket=actionButtons.results){
  const node=element('article',undefined,'card memory-card');
  node.append(element('small',(entry.origen==='approved'?'Fuente aprobada':'Fuente legada')+' · '+entry.tipo+' · '+entry.estado));
  node.append(element('h3',entry.titular||entry.id),element('code',entry.id));
  node.append(element('p','Área: '+(entry.area||'no declarada')+' · Versión: '+(entry.version===null?'no declarada':entry.version)));
  if(entry.estado_detalle)node.append(element('p','Estado declarado: '+entry.estado_detalle));
  if(entry.category!==null)node.append(element('p','Categoría: '+entry.category));
  node.append(element('p','Evidencia declarada: '+(entry.evidencia||'no declarada')));
  const source=element('details');source.append(element('summary','Procedencia de la lectura'),element('code',entry.ruta),element('code','SHA-256 del texto UTF-8: '+entry.source_sha256));node.append(source);
  const actions=element('div',undefined,'memory-actions');actions.append(action('Ver entrada','show',entry.id,bucket),action('Ver relaciones','related',entry.id,bucket));node.append(actions);
  return node;
 }
 function render(data){
  if(data.operation==='search'){
   for(const bucket of Object.values(actionButtons))bucket.clear();
   results.replaceChildren(...data.entries.map(entry=>card(entry)));selected.replaceChildren();relations.replaceChildren();
   resultsDate.textContent='Resultados obtenidos: '+data.observed_at;
  }else if(data.operation==='show'){
   actionButtons.selected.clear();actionButtons.related.clear();selected.replaceChildren();relations.replaceChildren();
   if(data.selected){const node=card(data.selected,actionButtons.selected);node.append(element('p','Entrada leída: '+data.observed_at),element('pre',data.selected.texto,'memory-body'));selected.append(node);selected.focus();}
  }else{
   actionButtons.related.clear();relations.replaceChildren();
   if(data.related){
    relations.append(element('h3','Relaciones declaradas'),element('p','Relaciones leídas: '+data.observed_at));
    for(const [group,label] of Object.entries(groups)){
     if(!data.related[group].length)continue;
     const block=element('section',undefined,'memory-relation-group');block.append(element('h4',label));
     for(const row of data.related[group]){
      if(group==='sucesion'){
       block.append(element('p',row.relation+' · '+row.id+(row.entry===null?' · sin resolver':'')));
       if(row.entry)block.append(card(row.entry,actionButtons.related));
      }else block.append(card(row,actionButtons.related));
     }
     relations.append(block);
    }
    relations.focus();
   }
  }
  if(data.status==='ambiguous'){actionButtons.selected.clear();actionButtons.related.clear();selected.replaceChildren();relations.replaceChildren();}
  last=data;freshness.textContent='Última consulta ('+data.operation+'): '+data.observed_at+' · '+data.budget.files+' archivos, '+data.budget.bytes+' bytes, '+data.budget.entries+' entradas de directorio.';
  if(data.status==='ambiguous')status.textContent='Identidad ambigua: existe una colisión. No se ha seleccionado ninguna entrada.';
  else if(data.status==='partial'||!data.complete)status.textContent='Lectura parcial: los límites o fallos impiden acreditar un corpus completo. Se muestran los datos disponibles.';
  else if(data.status==='not_found')status.textContent='No se encontraron entradas que coincidan con la consulta.';
  else status.textContent='Consulta local completada. Los estados y las relaciones conservan su procedencia declarada.';
 }
 function disabled(value){search.disabled=value;for(const bucket of Object.values(actionButtons))for(const button of bucket)button.disabled=value;}
 async function query(request){
  if(busy)return;
  const body=JSON.stringify(request);
  if(new TextEncoder().encode(body).length>4096){status.textContent='La consulta supera el límite de tamaño. Reduce los filtros.';return;}
  busy=true;disabled(true);const controller=new AbortController();const deadline=setTimeout(()=>controller.abort(),6000);
  try{
   const response=await fetch('api/memory',{method:'POST',headers:{'Content-Type':'application/json'},body,credentials:'omit',cache:'no-store',signal:controller.signal});
   if(!response.ok)throw Error('unavailable');
   const data=await response.json();
   if(controller.signal.aborted||!valid(data,request)||['unavailable','invalid_request'].includes(data.status))throw Error('unavailable');
   render(data);
  }catch{
   status.textContent=last?'No se pudo consultar. Se conserva la vista y su fecha anterior; no se acredita su vigencia.':'No se pudo consultar la memoria. Sin lectura disponible; vuelve a intentarlo.';
  }finally{clearTimeout(deadline);busy=false;disabled(false);}
 }
 form.addEventListener('submit',event=>{
  event.preventDefault();
  if(![text.value,area.value,type.value].every(value=>string(value,1000))){status.textContent='La consulta supera el límite de 1.000 caracteres por campo.';return;}
  query({operation:'search',text:text.value,area:area.value,tipo:type.value,limit:20});
 });
})();
