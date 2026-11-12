/** Offline authoring adapter. Sources arrive over stdin; never loads document resources. */
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createRequire} from 'node:module';
import {basename,join,resolve} from 'node:path';
import {readInput,closeOwnedBrowser} from './handbook-runtime.mjs';

const require=createRequire(import.meta.url);
const sha=data=>createHash('sha256').update(data).digest('hex');
const escape=value=>String(value).replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const CSP="default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'";

async function offline(page,{javascript=false}={}) {
  let blocked=0;
  await page.setJavaScriptEnabled(javascript);
  await page.setOfflineMode(true);
  await page.setBypassServiceWorker(true);
  await page.setRequestInterception(true);
  page.on('request',request=>{
    if(request.isInterceptResolutionHandled())return;
    let allowed=false;
    try {
      const url=new URL(request.url());
      allowed=url.href==='about:blank' || ['data:','blob:'].includes(url.protocol);
    } catch { /* deny malformed resources */ }
    if(!allowed)blocked++;
    Promise.resolve(allowed?request.continue():request.abort()).catch(()=>{});
  });
  return ()=>blocked;
}

async function renderDiagram(page,row,ordinal) {
  const svg=await page.evaluate(async ({code,id})=>{
    const result=await globalThis.mermaid.render(id,code);
    const parsed=new DOMParser().parseFromString(result.svg,'image/svg+xml');
    if(parsed.querySelector('parsererror'))throw new Error('diagram_invalid_svg');
    document.querySelector('#diagram').replaceChildren(document.importNode(parsed.documentElement,true));
    const element=document.querySelector('#diagram svg');
    if(!element)throw new Error('diagram_missing');
    // A fixed authoring width gives crisp, predictable PNGs in the final PDF.
    const view=element.viewBox.baseVal;
    if(!view.width || !view.height)throw new Error('diagram_dimensions');
    const width=Math.min(1000,Math.max(680,view.width));
    element.style.maxWidth='none';element.style.width=width+'px';
    element.style.height=(width*view.height/view.width)+'px';
    return {width:element.getBoundingClientRect().width,height:element.getBoundingClientRect().height};
  },{code:row.code,id:'handbookdiagram'+ordinal});
  if(svg.height>10000 || svg.width>2000)throw new Error('diagram_dimensions');
  await page.evaluate(()=>document.fonts.ready);
  const png=await page.$eval('#diagram svg',element=>{
    element.setAttribute('role','img');return true;
  }).then(()=>page.$('#diagram svg')).then(element=>element.screenshot({type:'png',omitBackground:false}));
  return {source:row.source,index:row.index,sha256:row.sha256,png_sha256:sha(png),
          width:svg.width,height:svg.height,data:'data:image/png;base64,'+Buffer.from(png).toString('base64')};
}

function documentHtml(edition,pictures,MarkdownIt,theme) {
  const toc=[];let figureOrdinal=0;
  const sections=edition.sections.map((section,sectionIndex)=>{
    const md=new MarkdownIt({html:false,linkify:false,typographer:false,breaks:false});
    const pictureMap=new Map(pictures.filter(row=>row.source===section.source).map(row=>[row.index,row]));
    let pictureIndex=0;let headingIndex=0;
    const originalFence=md.renderer.rules.fence;
    md.renderer.rules.fence=(tokens,index,options,env,self)=>{
      if(tokens[index].info.trim()!=='mermaid')return originalFence(tokens,index,options,env,self);
      const picture=pictureMap.get(++pictureIndex);
      if(!picture)throw new Error('diagram_mismatch');
      figureOrdinal++;
      return '<figure><img alt="Diagrama '+figureOrdinal+'" src="'+picture.data+'"><figcaption>Diagrama '+figureOrdinal+' · '+escape(section.source)+'</figcaption></figure>';
    };
    // Never fetch even an allowlisted document's linked image/file.
    md.renderer.rules.image=(tokens,index)=>'<span class="image-label">'+escape(tokens[index].content)+'</span>';
    let source=section.text;
    if(!section.source.endsWith('.md'))source='```'+(section.source.endsWith('.json')?'json':'text')+'\n'+source+'\n```\n';
    const tokens=md.parse(source,{});
    for(let i=0;i<tokens.length;i++) {
      if(tokens[i].type!=='heading_open')continue;
      const id='section'+sectionIndex+'heading'+(++headingIndex);
      tokens[i].attrSet('id',id);
      const label=tokens[i+1]?.content || section.source;
      if(['h1','h2'].includes(tokens[i].tag))toc.push({id,label,level:tokens[i].tag});
    }
    if(!headingIndex)toc.push({id:'section'+sectionIndex,label:section.source,level:'h1'});
    const body=md.renderer.render(tokens,md.options,{});
    if(pictureIndex!==pictureMap.size)throw new Error('diagram_mismatch');
    return '<section class="chapter" id="section'+sectionIndex+'"><div class="source-label">'+escape(section.source)+'</div>'+body+'</section>';
  }).join('\n');
  const contents=toc.map(row=>'<li class="'+row.level+'"><a href="#'+row.id+'">'+escape(row.label)+'</a></li>').join('');
  return '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="'+escape(CSP)+'"><title>'+escape(edition.title)+'</title><style>'+theme+'</style></head><body>'+
    '<header class="cover"><div class="brand">CUSTOM-AGENTS</div><div class="cover-line"></div><p class="eyebrow">Guías de trabajo · Edición '+escape(edition.edition)+'</p><h1>'+escape(edition.title)+'</h1><p class="lede">Recorridos, ejemplos y decisiones explicados paso a paso para las personas que utilizan el producto.</p><div class="cover-note">Consulta la versión del plugin y los requisitos del proveedor antes de ejecutar los ejemplos. Una conexión configurada no acredita permisos, cuota ni una entrega validada.</div></header>'+
    '<nav class="contents"><div class="eyebrow">Navegación</div><h1>Contenido</h1><p>Los enlaces del índice te llevan al apartado correspondiente. Markdown sigue siendo la fuente mantenida.</p><ul>'+contents+'</ul></nav><main>'+sections+'</main></body></html>';
}

async function main() {
  const input=await readInput(process.stdin);
  const request=JSON.parse(input);
  if(request.schema_version!==1 || request.editions?.length!==3)throw new Error('invalid_request');
  const tools=request.tools;
  const puppeteer=require(join(resolve(tools.node_modules),'puppeteer'));
  const MarkdownIt=require(join(resolve(tools.node_modules),'markdown-it'));
  const theme=await readFile(new URL('./handbook-theme.css',import.meta.url),'utf8');
  const mermaid=await readFile(tools.mermaid,'utf8');
  const browser=await puppeteer.launch({headless:true,...(tools.browser?{executablePath:tools.browser}:{}),
    args:['--disable-background-networking','--disable-component-update','--disable-sync','--no-first-run','--font-render-hinting=none']});
  const result={editions:[]};
  try {
    const diagramPage=await browser.newPage();
    const blockedDiagrams=await offline(diagramPage,{javascript:true});
    await diagramPage.setViewport({width:1200,height:1000,deviceScaleFactor:2});
    await diagramPage.setContent('<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#fff;font-family:Arial,sans-serif}#diagram{padding:20px;display:inline-block}svg{display:block}</style></head><body><div id="diagram"></div></body></html>',{waitUntil:'domcontentloaded'});
    await diagramPage.addScriptTag({content:mermaid});
    await diagramPage.evaluate(()=>globalThis.mermaid.initialize({startOnLoad:false,securityLevel:'strict',
      theme:'base',fontFamily:'Arial, sans-serif',themeVariables:{primaryColor:'#eef0ff',primaryTextColor:'#14233b',primaryBorderColor:'#5c5dcc',lineColor:'#687993',secondaryColor:'#e4f5f1',tertiaryColor:'#f4f6fa',fontSize:'16px'},
      flowchart:{htmlLabels:false,useMaxWidth:false,curve:'basis'},sequence:{useMaxWidth:false},maxTextSize:60000}));
    let ordinal=0;
    for(const edition of request.editions) {
      const pictures=[];
      for(const row of edition.diagrams) {
        ordinal++;
        try {pictures.push(await renderDiagram(diagramPage,row,ordinal));}
        catch {throw new Error('diagram_failed:'+ordinal);}
      }
      const page=await browser.newPage();
      const blocked=await offline(page);
      await page.setContent(documentHtml(edition,pictures,MarkdownIt,theme),{waitUntil:'load',timeout:60000});
      // Font readiness is observed via the protocol; document scripts stay disabled.
      await page.evaluate(()=>document.fonts.ready);
      const out=join(tools.stage,basename(edition.pdf));
      await page.pdf({path:out,format:'A4',printBackground:true,tagged:true,outline:true,
        margin:{top:'17mm',bottom:'18mm',left:'17mm',right:'17mm'},displayHeaderFooter:true,
        headerTemplate:'<div></div>',footerTemplate:'<div style="font-family:Arial;font-size:8px;color:#66758a;width:100%;padding:0 17mm;display:flex;justify-content:space-between"><span>custom-agents · '+escape(edition.edition)+'</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>'});
      if(blocked() || blockedDiagrams())throw new Error('blocked_resource');
      result.editions.push({pdf:edition.pdf,diagrams:pictures.map(({data,...row})=>row),blocked_resources:0});
      await page.close();
    }
    await writeFile(join(tools.stage,'render-result.json'),JSON.stringify(result));
  } finally {
    if(process.platform!=='win32' || process.env.CA_HANDBOOK_OWNED_JOB!=='1')await closeOwnedBrowser(browser);
  }
  await new Promise(resolve=>process.stdout.write(JSON.stringify(result),resolve));
  if(process.platform==='win32' && process.env.CA_HANDBOOK_OWNED_JOB==='1')process.exit(0);
}

main().catch(async error=>{
  // Do not echo a source body, local tool path, browser argument or parser excerpt.
  const known=new Set(['input_budget','invalid_request','diagram_dimensions','diagram_missing','diagram_mismatch','blocked_resource','browser_close_timeout']);
  await new Promise(resolve=>process.stderr.write('handbook-render: '+(known.has(error?.message) || /^diagram_failed:\d{1,3}$/.test(error?.message || '')?error.message:'conversion_failed'),resolve));
  process.exitCode=1;
  process.exit(1);
});
