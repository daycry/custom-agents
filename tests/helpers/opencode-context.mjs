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

// fix15 (gap 13): 120 s por defecto, acorde a la carga (con 12 bucles de CPU los tests que lanzan node en serie tardaban mas de 15 s: 2 de 44 en rojo);
// solo se agota cuando el efecto no ocurre, asi que no encarece los tests verdes.
export async function until(predicate, ms = 120000) {
  const deadline = Date.now() + ms;
  while (!predicate()) {
    if (Date.now() > deadline) throw new Error('Adapter effect was not observed');
    await new Promise(resolve => setTimeout(resolve, 25));
  }
}
