/* Safe DOM primitives. Repository and native text never enter innerHTML. */
const ns='http://www.w3.org/2000/svg'
export const $=id=>document.getElementById(id)
export const providers={'claude-code':'Claude Code',codex:'Codex',opencode:'OpenCode 2'}
export const busy=new Set(['connecting','sending','queued','running','waiting','interrupting','disconnecting'])
const states={
 connecting:['Conectando','active'],sending:['Enviando','active'],queued:['Esperando actividad','active'],
 running:['Trabajando','active'],waiting:['Necesita respuesta','warning'],interrupting:['Interrupción solicitada','warning'],disconnecting:['Cerrando conexión','neutral'],
 idle:['Disponible','success'],failed:['Falló','error'],interrupted:['Interrumpida','neutral'],
 uncertain:['Por confirmar','warning'],disconnected:['Sin conexión','neutral'],
 borrador:['Por preparar','neutral'],'en-progreso':['En marcha','active'],'en-revision':['En revisión','warning'],
 completado:['Completado','success'],cancelado:['Cancelado','neutral'],aprobada:['Aprobada','active'],
 implementada:['Implementada','success'],obsoleta:['Obsoleta','neutral'],sin_spec:['Sin definición','neutral']}
export function el(tag,text,cls){
 const node=document.createElement(tag)
 if(text!==undefined&&text!==null)node.textContent=String(text)
 if(cls)node.className=cls
 return node
}
export function icon(name){
 const svg=document.createElementNS(ns,'svg');svg.setAttribute('class','icon');svg.setAttribute('aria-hidden','true')
 const use=document.createElementNS(ns,'use');use.setAttribute('href','#i-'+name);svg.append(use);return svg
}
export function button(text,fn,cls='secondary',symbol){
 const node=el('button',undefined,'button '+cls);node.type='button'
 if(symbol)node.append(icon(symbol))
 node.append(document.createTextNode(text));if(fn)node.addEventListener('click',fn);return node
}
export function badge(value,label){
 const [text,cls]=states[value]||['Sin datos','neutral']
 return el('span',label||text,'badge '+cls)
}
export function provider(value){return el('span',value==='claude-code'?'C':value==='opencode'?'O':'X','provider-mark '+(providers[value]?value:''))}
export function time(value){
 const date=new Date(typeof value==='number'&&value<1e12?value*1000:value)
 return Number.isNaN(date.getTime())?'Sin fecha':new Intl.DateTimeFormat('es',{hour:'2-digit',minute:'2-digit'}).format(date)
}
export function relative(value){
 const date=new Date(typeof value==='number'&&value<1e12?value*1000:value)
 const seconds=Math.max(0,Math.floor((Date.now()-date.getTime())/1000))
 if(!Number.isFinite(seconds))return 'Sin fecha'
 if(seconds<60)return 'ahora'
 if(seconds<3600)return 'hace '+Math.floor(seconds/60)+' min'
 if(seconds<86400)return 'hace '+Math.floor(seconds/3600)+' h'
 return 'hace '+Math.floor(seconds/86400)+' días'
}
export function key(){return crypto.randomUUID().replaceAll('-','')}
export function loading(root,text='Preparando esta vista…'){root.replaceChildren(el('div',text,'loading'))}
export function empty(root,title,description,symbol='box',actions=[],compact=false){
 const box=el('div',undefined,'empty-state'+(compact?' compact':''))
 const mark=el('div',undefined,'illustration-icon');mark.append(icon(symbol))
 box.append(mark,el('h2',title),el('p',description))
 if(actions.length){const row=el('div',undefined,'empty-actions');row.append(...actions);box.append(row)}
 root.replaceChildren(box);return box
}
export function panel(title,subtitle,action){
 const box=el('section',undefined,'panel'),head=el('header',undefined,'panel-head'),copy=el('div')
 copy.append(el('h2',title));if(subtitle)copy.append(el('p',subtitle,'small-muted'))
 head.append(copy);if(action)head.append(action);box.append(head);return box
}
export function progress(value){
 const node=el('progress');node.max=100;node.value=Number.isFinite(value)?Math.max(0,Math.min(100,value)):0
 node.setAttribute('aria-label','Progreso '+node.value+' por ciento');return node
}
export function inline(node,text){
 const pattern=/(\x60([^\x60]+)\x60|\*\*([^*]+)\*\*|\[([^\]]+)\]\(([^)]+)\))/g
 let position=0
 for(const match of String(text).matchAll(pattern)){
  node.append(document.createTextNode(text.slice(position,match.index)))
  if(match[2])node.append(el('code',match[2]))
  else if(match[3])node.append(el('strong',match[3]))
  else{
   let safe=false
   try{const url=new URL(match[5],location.href);safe=['http:','https:'].includes(url.protocol)}catch{}
   if(safe){const link=el('a',match[4]);link.href=match[5];link.target='_blank';link.rel='noopener noreferrer';node.append(link)}
   else node.append(document.createTextNode(match[4]))
  }
  position=match.index+match[0].length
 }
 node.append(document.createTextNode(String(text).slice(position)))
}
export function markdown(text){
 const root=el('div',undefined,'markdown'),lines=String(text||'').split('\n')
 let paragraph=[],code=null,list=null
 const flush=()=>{if(paragraph.length){const p=el('p');inline(p,paragraph.join(' '));root.append(p);paragraph=[]}list=null}
 for(const line of lines){
  if(line.startsWith('\x60\x60\x60')){
   flush()
   if(code!==null){const pre=el('pre');pre.append(el('code',code.join('\n')));root.append(pre);code=null}
   else code=[]
   continue
  }
  if(code!==null){code.push(line);continue}
  if(!line.trim()){flush();continue}
  const heading=line.match(/^(#{1,4})\s+(.+)$/)
  if(heading){flush();const h=el('h'+Math.min(heading[1].length+1,4));inline(h,heading[2]);root.append(h);continue}
  const bullet=line.match(/^\s*(?:[-*]|\d+\.)\s+(.+)$/)
  if(bullet){if(paragraph.length)flush();if(!list){list=el('ul');root.append(list)}const li=el('li');inline(li,bullet[1]);list.append(li);continue}
  if(line.startsWith('> ')){flush();const quote=el('blockquote');inline(quote,line.slice(2));root.append(quote);continue}
  paragraph.push(line)
 }
 flush()
 if(code!==null){const pre=el('pre');pre.append(el('code',code.join('\n')));root.append(pre)}
 return root
}
export function fieldLabel(label,value){
 const box=el('div');box.append(el('dt',label),el('dd',value??'Sin datos'));return box
}

