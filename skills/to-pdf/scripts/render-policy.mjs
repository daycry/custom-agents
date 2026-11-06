/** Explicit document execution/resource policy. No filesystem or network side effects. */
export function parseArgs(argv) {
  const args={_:[],allowJs:false,unsafeNoSandbox:false,origins:[]}
  const values=new Map([['--out','out'],['--theme','theme'],['--title','title']])
  for(let i=0;i<argv.length;i++) {
    const arg=argv[i]
    if(arg==='--'){args._.push(...argv.slice(i+1));break}
    if(arg==='--allow-js'){args.allowJs=true;continue}
    if(arg==='--unsafe-no-sandbox'){args.unsafeNoSandbox=true;continue}
    if(arg==='--allow-origin' || values.has(arg)) {
      const value=argv[++i]
      if(value===undefined || value.startsWith('--'))throw new Error('Falta valor de '+arg)
      if(arg==='--allow-origin')args.origins.push(validateOrigin(value))
      else args[values.get(arg)]=value
    } else if(arg.startsWith('-'))throw new Error('Opción desconocida: '+arg)
    else args._.push(arg)
  }
  if(args._.length!==1)throw new Error('Indica exactamente un documento de entrada')
  args.origins=[...new Set(args.origins)]
  return args
}
function validateOrigin(value) {
  let url
  try {url=new URL(value)}catch {throw new Error('Origen no válido')}
  if(url.protocol!=='https:' || url.username || url.password || url.pathname!=='/' || url.search || url.hash)
    throw new Error('--allow-origin requiere un origen HTTPS sin ruta, credenciales ni parámetros')
  return url.origin
}
export function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]))
}
export function browserOptions(options) {
  const args=['--font-render-hinting=none','--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run','--force-webrtc-ip-handling-policy=disable_non_proxied_udp']
  if(options.unsafeNoSandbox)args.push('--no-sandbox','--disable-setuid-sandbox')
  return {headless:true,args}
}
export async function applyPolicy(page,options) {
  const origins=new Set(options.origins),state={blocked:0,error:null}
  await page.setJavaScriptEnabled(options.allowJs)
  await page.setOfflineMode(origins.size===0)
  await page.setBypassServiceWorker(true)
  await page.setRequestInterception(true)
  page.on('request',request=>{
    if(request.isInterceptResolutionHandled())return
    let allowed=false
    try {
      const url=new URL(request.url())
      allowed=['data:','blob:'].includes(url.protocol) || url.href==='about:blank' ||
        url.protocol==='https:' && !url.username && !url.password && origins.has(url.origin)
    } catch { /* malformed URLs are denied */ }
    if(!allowed)state.blocked++
    Promise.resolve(allowed?request.continue():request.abort()).catch(error=>{state.error=error})
  })
  return {
    get blocked(){return state.blocked},
    check(){if(state.error)throw new Error('No se pudo aplicar la política de recursos del PDF')},
  }
}
