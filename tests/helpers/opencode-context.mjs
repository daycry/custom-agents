// Double of public V2 domains; native loading and dispatch are checked separately.
export function opencodeContext(directory) {
  const hooks = new Map(), pending = [];
  let wake, stopped = false;
  const location = { directory };
  return {
    location, hooks,
    tool: { hook: async (name, fn) => { hooks.set(`tool.${name}`, fn); } },
    session: {
      hook: async (name, fn) => { hooks.set(`session.${name}`, fn); },
      get: async () => ({ location, data: { location } }),
    },
    event: {
      subscribe({ signal }) {
        signal.addEventListener('abort', () => { stopped = true; wake?.(); }, { once: true });
        return (async function* () {
          while (!stopped) {
            if (!pending.length) await new Promise(resolve => { wake = resolve; });
            if (!stopped && pending.length) yield pending.shift();
          }
        })();
      },
    },
    emit(event) { pending.push(event); wake?.(); },
    get stopped() { return stopped; },
  };
}

export async function until(predicate) {
  const deadline = Date.now() + 15000;
  while (!predicate()) {
    if (Date.now() > deadline) throw new Error('Adapter effect was not observed');
    await new Promise(resolve => setTimeout(resolve, 25));
  }
}
