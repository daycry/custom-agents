/* Native signal freshness is independent of HTTP success and page visibility. */
(()=>{
'use strict';
const byId=id=>document.getElementById(id);
const cards=byId('activity-cards'),status=byId('activity-status'),freshness=byId('activity-freshness'),refresh=byId('activity-refresh'),coverage=byId('activity-coverage');
if(!cards||!status||!freshness||!refresh||!coverage)return;
const roles=new Set(['analyst','evaluator','architect','planner','implementer','reviewer','qa','documenter','knowledge-curator','nemesis','other']);
const states={recent_start:'Señal reciente de inicio',recent_response_end:'Fin reciente de respuesta',recent_execution_end:'Fin reciente de ejecución',recent_idle:'Señal reciente de inactividad',unknown:'Estado desconocido'};
const reasons=new Set(['disabled','invalid_config','state_missing','unowned_state','invalid_state','unsafe_state','state_busy','deadline_exceeded','state_budget','durability_degraded','invalid_input','input_budget','project_mismatch','unsupported_event','invalid_identity','role_map_unavailable','quota_exceeded','revision_exhausted','invalid_clock','reader_unavailable','invalid_snapshot','response_budget']);
const keys=['runtime','scope','session_key','agent_key','role','source','observed_at','revision','age_seconds','state','live_process_proven','agent_destroyed_proven'];
const shape=(value,fields)=>value!==null&&typeof value==='object'&&!Array.isArray(value)&&Object.keys(value).length===fields.length&&fields.every(key=>Object.hasOwn(value,key));
const number=value=>typeof value==='number'&&Number.isFinite(value)&&value>=0&&value<=Number.MAX_SAFE_INTEGER;
const key=value=>typeof value==='string'&&/^[a-f0-9]{64}$/.test(value);
const identity=row=>[row.runtime,row.scope,row.session_key,row.agent_key].join(':');
function validRow(row){
 if(!shape(row,keys)||!['claude','codex','opencode'].includes(row.runtime)||!key(row.session_key)||!number(row.observed_at)||!Number.isSafeInteger(row.revision)||row.revision<1||!(row.age_seconds===null||number(row.age_seconds))||!Object.hasOwn(states,row.state)||row.live_process_proven!==false||row.agent_destroyed_proven!==false)return false;
 if((row.age_seconds===null||row.age_seconds>=60)&&row.state!=='unknown')return false;
 if(row.scope==='subagent')return ['claude','codex'].includes(row.runtime)&&key(row.agent_key)&&roles.has(row.role)&&row.source==='native_hook'&&['recent_start','recent_response_end','unknown'].includes(row.state);
 return row.scope==='session'&&row.agent_key===null&&row.role===null&&row.source===(row.runtime==='opencode'?'native_stream':'native_hook')&&['recent_start','recent_execution_end','recent_idle','unknown'].includes(row.state);
}
function valid(data){
 if(!shape(data,['schema_version','status','reason','complete','collection_complete','observations'])||data.schema_version!==1||data.collection_complete!==false||!Array.isArray(data.observations)||data.observations.length>64)return false;
 if(data.status!=='ok')return ['unavailable','invalid_snapshot'].includes(data.status)&&reasons.has(data.reason)&&data.complete===false&&data.observations.length===0;
 return data.reason===null&&data.complete===true&&data.observations.every(validRow)&&new Set(data.observations.map(identity)).size===data.observations.length;
}
let rows=[],poll=null,expiry=null,busy=false,controller=null,resume=false,generation=0;
const age=(entry,now)=>entry.age===null?Infinity:entry.age+Math.max(0,now-entry.received)/1000;
function date(value){const result=new Date(value*1000);return Number.isNaN(result.getTime())?'Fecha no representable':result.toISOString();}
function render(){
 clearTimeout(expiry);expiry=null;const now=performance.now();let next=Infinity;
 const elements=rows.map(entry=>{
  const row=entry.row,current=age(entry,now),state=current>=60?'unknown':row.state;
  if(state!=='unknown')next=Math.min(next,(60-current)*1000);
  const article=document.createElement('article');article.className='card';
  const title=document.createElement('h3');title.textContent=row.runtime+' · '+(row.scope==='session'?'Sesión':row.role);
  const signal=document.createElement('p');signal.textContent=states[state];
  const timestamp=document.createElement('p');timestamp.textContent='Señal recibida: '+date(row.observed_at);
  const source=document.createElement('p');source.textContent='Fuente: '+(row.source==='native_hook'?'Hook nativo':'Flujo nativo')+' · Identidad y rol declarados';
  article.append(title,signal,timestamp,source);return article;
 });
 cards.replaceChildren(...elements);
 if(Number.isFinite(next))expiry=setTimeout(render,Math.max(1,next));
}
function accept(data){
 const now=performance.now(),previous=new Map(rows.map(entry=>[identity(entry.row),entry]));
 rows=data.observations.map(row=>{
  const old=previous.get(identity(row));let advertised=row.age_seconds;
  if(old&&old.row.revision===row.revision&&old.row.observed_at===row.observed_at){const elapsed=age(old,now);advertised=advertised===null||!Number.isFinite(elapsed)?null:Math.max(advertised,elapsed);}
  return {row,age:advertised,received:now};
 });
 freshness.textContent='Última lectura de señales: '+new Date().toISOString();
 status.textContent=rows.length?'Señales leídas; la frescura no acredita presencia.':'Lectura válida sin señales registradas; colección incompleta.';
 render();
}
async function request(){
 if(busy||document.hidden)return;
 clearTimeout(poll);poll=null;busy=true;refresh.disabled=true;controller=new AbortController();const own=controller,version=++generation;
 const timeout=setTimeout(()=>own.abort(),4000);
 try{
  const response=await fetch('api/activity',{method:'GET',credentials:'omit',cache:'no-store',signal:own.signal});
  if(!response.ok)throw Error('unavailable');const data=await response.json();
  if(own.signal.aborted||version!==generation)return;
  if(valid(data)&&data.status==='unavailable'&&data.reason==='disabled'){
   rows=[];render();status.textContent='La actividad de los agentes está desactivada (opt-in). Para activarla, define "sesion": {"actividad": true} en .claude/dev.json.';return;
  }
  if(!valid(data)||data.status!=='ok')throw Error('unavailable');accept(data);
 }catch(error){if(version===generation)status.textContent='No se pudo actualizar; se conserva la última vista y sus señales caducan.';render();}
 finally{
  clearTimeout(timeout);busy=false;controller=null;refresh.disabled=false;
  if(!document.hidden){if(resume){resume=false;request();}else poll=setTimeout(request,5000);}
 }
}
coverage.textContent='collection_complete: false · Colección incompleta; no representa todos los agentes o sesiones.';
refresh.addEventListener('click',request);
document.addEventListener('visibilitychange',()=>{
 render();clearTimeout(poll);poll=null;
 if(document.hidden){resume=false;++generation;if(controller)controller.abort();}
 else if(busy)resume=true;else request();
});
request();
})();
