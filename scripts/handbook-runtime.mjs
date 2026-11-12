/** Dependency-free boundaries of the optional handbook authoring process. */
export async function readInput(stream,maximum=8*1024*1024) {
  let input='';
  stream.setEncoding('utf8');
  for await(const chunk of stream) {
    input+=chunk;
    if(Buffer.byteLength(input)>maximum)throw new Error('input_budget');
  }
  return input;
}

export async function closeOwnedBrowser(browser,timeout=5000) {
  const bounded=async promise=>{
    let timer;
    try {return await Promise.race([promise,new Promise(resolve=>{timer=setTimeout(()=>resolve('timeout'),timeout)})]);}
    finally {clearTimeout(timer);}
  };
  const outcome=await bounded(Promise.resolve().then(()=>browser.close()).then(()=> 'closed',()=> 'failed'));
  if(outcome==='closed')return {forced:false};
  // A graceful-close failure remains RED. The Python parent terminates only its
  // already owned process group/job; no browser PID search or hidden green.
  throw new Error('browser_close_timeout');
}
