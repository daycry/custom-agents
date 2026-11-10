import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {reconcileChildren,newMessageAnnouncements} from '../skills/plugin-panel/assets/console-dom.js'

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
 const seen=new Set()
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
