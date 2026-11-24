import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {reconcileChildren,newMessageAnnouncements} from '../skills/plugin-panel/assets/console-dom.js'
import {createContext} from '../skills/plugin-panel/assets/console-context.js'

// A minimal parent: it records every insertion and removal, which is what a screen reader reacts to.
function parent(children){
 const log=[]
 const node={children:[...children],log,
  removeChild(child){log.push(['remove',child]);this.children.splice(this.children.indexOf(child),1)},
  insertBefore(child,before){
   log.push(['insert',child]);const at=this.children.indexOf(child);if(at>=0)this.children.splice(at,1)
   const to=before?this.children.indexOf(before):this.children.length;this.children.splice(to,0,child)}}
 return node
}

test('f4fix1 gap 6: a poll with a new message only inserts that message',()=>{
 const [a,b,c]=['a','b','c'].map(name=>({name}))
 const root=parent([a,b])
 reconcileChildren(root,[a,b,c])
 assert.deepEqual(root.log,[['insert',c]])
 assert.deepEqual(root.children,[a,b,c])
})

test('f4fix1 gap 6: an unchanged list is not touched and a dropped node is the only removal',()=>{
 const [a,b,c]=['a','b','c'].map(name=>({name}))
 const root=parent([a,b,c])
 reconcileChildren(root,[a,b,c])
 assert.deepEqual(root.log,[])
 reconcileChildren(root,[a,c])
 assert.deepEqual(root.log,[['remove',b]])
 assert.deepEqual(root.children,[a,c])
})

test('f4fix1 gap 6: only the new assistant messages are announced, once',()=>{
 const seen=new Map()
 const history=[{id:'1',role:'user',text:'hola'},{id:'2',role:'assistant',text:'respuesta uno'}]
 assert.deepEqual(newMessageAnnouncements(seen,history),['respuesta uno'])      // the first call reads history
 assert.deepEqual(newMessageAnnouncements(seen,history),[])                    // the next poll repeats nothing
 const next=[...history,{id:'3',role:'user',text:'otra'},{id:'4',role:'assistant',text:'x'.repeat(500)}]
 const fresh=newMessageAnnouncements(seen,next)
 assert.equal(fresh.length,1)
 assert.equal(fresh[0].length,280)
})

test('f4fix1 gap 6: the log is not a live region and a separate one carries the news',()=>{
 const html=readFileSync(new URL('../skills/plugin-panel/assets/control-center.html',import.meta.url),'utf8')
 const log=html.match(/<div id="chat-messages"[^>]*>/)[0]
 assert.ok(!log.includes('aria-live="polite"'))
 assert.ok(log.includes('aria-live="off"'))
 const live=html.match(/<div id="chat-live"[^>]*>/)[0]
 assert.ok(live.includes('aria-live="polite"')&&live.includes('sr-only'))
 const sessions=readFileSync(new URL('../skills/plugin-panel/assets/console-sessions.js',import.meta.url),'utf8')
 assert.ok(!/root\.replaceChildren\(\.\.\.desired\)/.test(sessions))
})

test('f4fix2 gap 3: a streamed answer is announced as it grows, never only its first fragment',()=>{
 const seen=new Map()
 const turn=text=>[{id:'u',role:'user',text:'hola'},{id:'a',role:'assistant',text}]
 assert.deepEqual(newMessageAnnouncements(seen,turn('Primera parte.')),['Primera parte.'])
 assert.deepEqual(newMessageAnnouncements(seen,turn('Primera parte.')),[])                       // same poll twice: silence
 assert.deepEqual(newMessageAnnouncements(seen,turn('Primera parte. Segunda parte.')),['Segunda parte.'])
 assert.deepEqual(newMessageAnnouncements(seen,turn('Primera parte. Segunda parte. Final.')),['Final.'])
})

test('f4fix2 gap 3: an empty first fragment does not hide the answer',()=>{
 const seen=new Map()
 const turn=text=>[{id:'a',role:'assistant',text}]
 assert.deepEqual(newMessageAnnouncements(seen,turn('')),[])
 assert.deepEqual(newMessageAnnouncements(seen,turn('   ')),[])
 assert.deepEqual(newMessageAnnouncements(seen,turn('Ya hay respuesta.')),['Ya hay respuesta.'])
 assert.deepEqual(newMessageAnnouncements(seen,turn('Otra versión distinta.')),['Otra versión distinta.'])   // rewritten text: announce it whole
})

test('T-40 fix1 gap 2: Activity renders a transition and keeps its row on an unchanged poll',async t=>{
 class Element {
  children=[];dataset={};style={};textContent=''
  constructor(tag){this.tagName=tag}
  append(...children){this.children.push(...children)}
  prepend(child){this.children.unshift(child)}
  replaceChildren(...children){this.children=children}
  get childElementCount(){return this.children.length}
  querySelector(selector){return selector==='[data-task-transitions]'
   ?this.children.find(child=>Object.hasOwn(child.dataset,'taskTransitions')):undefined}
  setAttribute(){}
  addEventListener(){}
 }
 const root=new Element('main')
 // The legacy replacement path updates the actual fixture so the assertion detects DOM churn.
 Element.prototype.replaceWith=function(node){root.children[root.children.indexOf(this)]=node}
 const doc={getElementById:()=>root,createElement:tag=>new Element(tag),
  createElementNS:(_,tag)=>new Element(tag),createTextNode:text=>({textContent:text})}
 const previous=globalThis.document
 globalThis.document=doc
 t.after(()=>{globalThis.document=previous})
 const now=Date.UTC(2026,10,24,10,0,0)
 t.mock.method(Date,'now',()=>now)
 const observed_at=now/1000-120
 const history={status:'ok',task_transitions:[{task:'T-40',from:'en-progreso',to:'en-revision',
  role:'implementer',runtime:'codex',source:'usage-meter',observed_at}]}
 const context=createContext({state:{epoch:1,view:'activity'},notice(){},safe:fn=>fn,
  api:async key=>key==='activity'?history:{sessions:[]}})
 await context.activity()
 const row=()=>root.querySelector('[data-task-transitions]').children[1].children[0]
 const initial=row(),[copy,when]=initial.children
 assert.equal(copy.children[0].textContent,'T-40 · En marcha → En revisión')
 assert.equal(copy.children[1].textContent,'implementer · Codex · usage-meter')
 assert.equal(when.dateTime,new Date(observed_at*1000).toISOString())
 assert.match(when.textContent,/hace 2 min$/)
 await context.activity()
 assert.ok(row()===initial,'an unchanged transition row was replaced')
})
