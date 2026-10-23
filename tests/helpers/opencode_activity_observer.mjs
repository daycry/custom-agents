// Test-only V2 context. Executes the real owned adapter and shared launcher.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import adapter from '../../hooks/opencode-plugin.js';
const root = process.argv[2], foreign = process.argv[3];
const location = { directory: root, workspaceID: 'own-workspace' };
const hooks = new Map(), queue = [];
let wake, aborted = false, foreignChecked = false;
const ctx = { location,
  tool: { hook: async (name, callback) => hooks.set('tool.' + name, callback) },
  session: { hook: async (name, callback) => hooks.set('session.' + name, callback),
    get: async ({ sessionID }) => {
      if (sessionID === 'foreign') { foreignChecked = true; return { location: { directory: foreign, workspaceID: 'own-workspace' } }; }
      return { location };
    } },
  event: { subscribe({ signal }) {
    signal.addEventListener('abort', () => { aborted = true; wake?.(); }, { once: true });
    return (async function* () {
      while (!aborted) { if (!queue.length) await new Promise(resolve => { wake = resolve; }); if (!aborted && queue.length) yield queue.shift(); }
    })();
  } },
};
const emit = event => { queue.push(event); wake?.(); };
const state = join(root, '.claude', 'agent-activity', 'snapshot.json');
async function until(predicate) {
  const end = Date.now() + 6000;
  while (!(await predicate())) { assert(Date.now() < end, 'activity adapter effect not observed'); await new Promise(resolve => setTimeout(resolve, 20)); }
}
const cleanup = await adapter.setup(ctx);
try {
  emit({ type: 'session.execution.succeeded', data: { sessionID: 'own-session', message: 'RAW-MESSAGE-FORBIDDEN' } });
  await until(async () => JSON.parse(await readFile(state, 'utf8')).records.some(row => row.runtime === 'opencode' && row.event === 'execution_finished'));
  emit({ type: 'session.status', data: { sessionID: 'own-session', status: { type: 'idle' } } });
  await until(async () => JSON.parse(await readFile(state, 'utf8')).records.some(row => row.runtime === 'opencode' && row.event === 'session_idle'));
  emit({ type: 'session.execution.failed', data: { sessionID: 'foreign' } });
  await until(async () => foreignChecked);
} finally { await cleanup(); }
assert(aborted);
process.stdout.write(JSON.stringify({ foreign_location_checked: foreignChecked, cleanup_completed: true, subagent_callbacks_invented: false }) + '\n');
