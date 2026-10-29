// OpenCode V2 server plugin. Business rules remain in the shared hook services.
import { execFile, spawn } from 'node:child_process';
import { constants, existsSync } from 'node:fs';
import { lstat, open, readdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const home = process.env.HOME || process.env.USERPROFILE || '.';
// --8<-- native protected role selection
const PROTECTED_GUARD_ROLES = ['implementer', 'architect'];

function nativeProtectedIDs(mapping, runtime) {
  const roles = mapping?.runtimes?.[runtime];
  if (!['claude', 'codex', 'opencode'].includes(runtime) || mapping?.schema_version !== 1
      || !Object.hasOwn(mapping?.runtimes || {}, runtime)
      || !roles || typeof roles !== 'object' || Array.isArray(roles)
      || PROTECTED_GUARD_ROLES.some(role => !Object.hasOwn(roles, role) || typeof roles[role] !== 'string' || !roles[role])) return null;
  const ids = new Set(PROTECTED_GUARD_ROLES.map(role => roles[role]));
  return ids.size === PROTECTED_GUARD_ROLES.length ? ids : null;
}
// --8<-- fin native protected role selection
// custom-agents hook-catalog:start
const hookCatalog = JSON.parse(`{
  "schema_version": 1,
  "bindings": [
    {"id":"guard","domain":"tool","native_event":"execute.before","event":"PreToolUse","handlers":["native-guardrail"],"timeout_ms":10500,"behavior":"guard","activation":"Exact own implementer and architect agent IDs; current project location"},
    {"id":"prompt","domain":"session","native_event":"prompt","event":"UserPromptSubmit","handlers":["user-prompt-capture.sh"],"timeout_ms":20000,"behavior":"informative","activation":"Text prompt in the current project location"},
    {"id":"context","domain":"session","native_event":"context","event":"SessionStart","handlers":["session-context.sh"],"timeout_ms":20000,"behavior":"informative","activation":"System context array in the current project location; unchanged context may reuse its cache"},
    {"id":"post","domain":"tool","native_event":"execute.after","event":"PostToolUse","handlers":["mark-docs-pending.sh","ledger-post.py"],"timeout_ms":20000,"behavior":"informative","activation":"Completed writing tool in the current project location","tools":["edit","write","patch","multiedit","apply_patch"]},
    {"id":"capture","domain":"event","native_events":["session.execution.succeeded","session.execution.failed","session.execution.interrupted","session.idle"],"idle_status_event":"session.status","idle_status":"idle","event":"SessionEnd","handlers":["session-journal.sh"],"timeout_ms":20000,"behavior":"informative","activation":"Execution/idle stream observation in the current project location; not a teardown hook"},
    {"id":"tool-activity","domain":"tool","native_event":"execute.after","event":"PostToolUse","handlers":["agent-activity"],"timeout_ms":2500,"behavior":"informative","activation":"Opt-in tool observation after exact project location verification; dispatched without waiting for the child"},
    {"id":"activity","domain":"event","native_events":["session.execution.started","session.execution.succeeded","session.execution.failed","session.execution.interrupted","session.idle"],"idle_status_event":"session.status","idle_status":"idle","event":"ActivityObserved","handlers":["agent-activity"],"timeout_ms":2500,"behavior":"informative","activation":"Opt-in execution start/end and idle observations after exact project location verification; not liveness or teardown"}
  ]
}`);
// custom-agents hook-catalog:end
const bindings = Object.fromEntries(hookCatalog.bindings.map(binding => [binding.id, binding]));
const writing = new Set(bindings.post.tools);
const readOnly = new Set(['read', 'glob', 'grep', 'list', 'ls', 'webfetch', 'websearch']);
// Only what the store's summary whitelist reads crosses to the activity child (agent-activity-store.py
// `_raw_summary`); file contents, outputs and the rest of the arguments stay here.
const summaryKeys = ['command', 'cmd', 'paths', 'files', 'file_path', 'notebook_path', 'filePath', 'path',
  'pattern', 'url', 'query', 'subagent_type', 'agent_type', 'skill', 'name'];
function summaryArgs(input) {
  const args = {};
  if (!input || typeof input !== 'object' || Array.isArray(input)) return args;
  for (const key of summaryKeys) {
    const value = input[key];
    if (typeof value === 'string') args[key] = value.slice(0, 8192);
    else if (Array.isArray(value) && value.length <= 1024 && value.every(item => typeof item === 'string'))
      args[key] = value.map(item => item.slice(0, 4096));
  }
  const patch = input.patchText ?? input.patch;
  if (args.command === undefined && typeof patch === 'string') {
    const files = patch.split('\n').map(line => line.trimStart())
      .filter(line => /^\*\*\* (?:Add|Update|Delete) File: /.test(line)).slice(0, 1024);
    if (files.length) args.command = files.join('\n');
  }
  return args;
}
const normalized = path => process.platform === 'win32' ? resolve(path).toLowerCase() : resolve(path);
const sameLocation = (a, b) => typeof a?.directory === 'string' && typeof b?.directory === 'string'
  && normalized(a.directory) === normalized(b.directory) && a.workspaceID === b.workspaceID;

export default {
  id: 'custom-agents',
  async setup(ctx) {
    const location = ctx.location;
    const roots = [join(here, '..', '..'), join(here, '..'), here,
      join(location.directory, '.opencode'), join(location.directory, '.claude'),
      join(home, '.config', 'opencode'), join(home, '.claude')];
    const hooks = roots.map(root => join(root, 'hooks')).find(dir => existsSync(join(dir, 'run-hook.mjs')));
    if (!hooks) { console.warn('custom-agents: hook bundle unavailable'); return; }
    const controller = new AbortController();
    const children = new Set(), inflight = new Set();
    let cached, generation = 0;
    const invalidate = () => { cached = undefined; generation++; };
    const warn = () => console.warn('custom-agents: informational hook unavailable; continuing');
    const warnGuard = () => console.warn('custom-agents: role guard unavailable; normal permissions continue');
    // Re-read the generated map for each decision; an uncertain map delegates to Python.
    async function loadGuardedIDs() {
      try {
        const path = join(hooks, '..', 'agent-kits', 'shared', 'native-roles.json');
        const info = await lstat(path);
        if (!info.isFile() || info.size > 65536) return;
        const flags = constants.O_RDONLY | (constants.O_NONBLOCK || 0) | (constants.O_NOFOLLOW || 0);
        const file = await open(path, flags);
        try {
          const opened = await file.stat();
          if (!opened.isFile() || opened.size > 65536) return;
          const buffer = Buffer.alloc(65537);
          let size = 0, read;
          while (size < buffer.length && (read = (await file.read(buffer, size, buffer.length - size, size)).bytesRead) > 0) size += read;
          if (size > 65536) return;
          const mapping = JSON.parse(new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(buffer.subarray(0, size)));
          return nativeProtectedIDs(mapping, 'opencode') || undefined;
        } finally { await file.close(); }
      } catch { /* The contained Python dispatcher owns diagnostics. */ }
    }
    if (!await loadGuardedIDs()) warnGuard();

    // Only metadata is scanned; unsafe or oversized trees disable reuse.
    async function signature(cwd) {
      const deadline = Date.now() + 250, rows = [];
      let count = 0;
      async function visit(path, depth = 0, top = false) {
        if (++count > 4096 || depth > 8 || Date.now() > deadline) throw new Error('cache bound');
        let info;
        try { info = await lstat(path); }
        catch (error) { if (error.code === 'ENOENT') { rows.push([path, 'missing']); return; } throw error; }
        if (info.isSymbolicLink()) throw new Error('cache link');
        rows.push([path, info.dev, info.ino, info.size, info.mtimeMs, info.ctimeMs]);
        if (!info.isDirectory()) return;
        const names = await readdir(path, { withFileTypes: true });
        if (names.length > 4096) throw new Error('cache bound');
        names.sort((a, b) => a.name.localeCompare(b.name));
        for (const entry of names) {
          if (!top || !entry.isDirectory() || entry.name === 'journal') await visit(join(path, entry.name), depth + 1);
        }
      }
      try {
        const config = join(cwd, '.claude', 'dev.json');
        let file;
        try {
          const info = await lstat(config);
          if (!info.isFile() || info.isSymbolicLink() || info.size > 65536) return null;
          file = await open(config, 'r');
          const buffer = Buffer.alloc(65537);
          const { bytesRead } = await file.read(buffer, 0, buffer.length, 0);
          if (bytesRead > 65536) return null;
          const configValue = JSON.parse(buffer.subarray(0, bytesRead).toString('utf8').replace(/^\uFEFF/, ''));
          if (configValue?.sesion?.journal?.dir) return null;
        } catch (error) { if (error.code !== 'ENOENT') return null; }
        finally { await file?.close(); }
        await visit(join(cwd, '.claude'), 0, true);
        await visit(join(cwd, 'docs', 'roadmap'));
        await visit(join(cwd, 'docs', 'knowledge'));
        return JSON.stringify(rows);
      } catch { return null; }
    }

    // Session APIs may expose other locations. Never reuse the instance root without checking.
    async function project(sessionID) {
      if (!sessionID || controller.signal.aborted) return null;
      const response = await ctx.session.get({ sessionID });
      const session = response?.data ?? response;
      return sameLocation(session?.location, location) ? session.location.directory : null;
    }

    function run(script, payload) {
      return new Promise(resolveResult => {
        if (controller.signal.aborted) return resolveResult('');
        const guard = script === 'native-guardrail', report = guard ? warnGuard : warn;
        let child, timer, finished = false, output = '', diagnostic = false, cancelled = false, stopping;
        let settle;
        const done = new Promise(resolveDone => { settle = resolveDone; });
        const entry = { done, stop: () => {
          if (stopping) return stopping;
          cancelled = true;
          stopping = new Promise(resolveStop => {
            if (!child?.pid) return resolveStop();
            if (process.platform === 'win32') {
              const taskkill = join(process.env.SystemRoot || process.env.WINDIR || 'C:\\Windows', 'System32', 'taskkill.exe');
              execFile(taskkill, ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true }, () => resolveStop());
            } else {
              try { process.kill(-child.pid, 'SIGKILL'); } catch { try { child.kill('SIGKILL'); } catch {} }
              resolveStop();
            }
          });
          return stopping;
        } };
        const finish = value => {
          if (finished) return;
          finished = true; clearTimeout(timer); children.delete(entry); settle(); resolveResult(value);
        };
        try {
          child = spawn('node', [join(hooks, 'run-hook.mjs'), script, '--runtime=opencode'], {
            cwd: payload.cwd, windowsHide: true, detached: process.platform !== 'win32',
            env: { ...process.env, CLAUDE_PROJECT_DIR: payload.cwd, CUSTOM_AGENTS_HOOK_OWN_GROUP: '1' },
            stdio: ['pipe', 'pipe', 'pipe'],
          });
          children.add(entry);
          const budget = hookCatalog.bindings.find(binding => binding.handlers.includes(script)).timeout_ms;
          timer = setTimeout(() => { report(); void entry.stop(); }, budget);
          child.stdout.setEncoding('utf8');
          child.stdout.on('data', chunk => {
            if (cancelled) return;
            output += chunk;
            if (output.length > 65536) { output = ''; report(); void entry.stop(); }
          });
          child.stderr.on('data', () => { diagnostic = true; }); // Never log payloads or consumer paths.
          child.stdin.on('error', () => {});
          child.on('error', () => { diagnostic = true; report(); });
          child.on('close', async code => { await stopping; if (code || (!guard && diagnostic)) report(); finish(code || cancelled ? '' : output); });
          child.stdin.end(JSON.stringify(payload), 'utf8');
        } catch { report(); if (child?.pid) void entry.stop(); else finish(''); }
      });
    }

    const callbacks = { guard: async event => {
      let decision;
      try {
        const guardedIDs = await loadGuardedIDs();
        if (guardedIDs && (!Object.hasOwn(event || {}, 'agent')
            || (typeof event.agent === 'string' && !guardedIDs.has(event.agent)))) return;
        const cwd = await project(event.sessionID);
        if (!cwd) return;
        const output = await run(bindings.guard.handlers[0], {
          agent: event.agent, tool_name: event.tool, tool_input: event.input, cwd,
        });
        decision = JSON.parse(output);
        if (!['deny', 'continue'].includes(decision?.decision)) throw new Error('guard result');
        if (decision.decision === 'deny' && (typeof decision.reason !== 'string' || !decision.reason.trim()))
          throw new Error('guard result');
        if (decision.diagnostic === 'guardrails-disabled') console.warn('custom-agents: role guards disabled by project configuration');
        else if (decision.diagnostic) warnGuard();
      } catch { warnGuard(); return; }
      // A before-hook Error is a native tool failure; no decision is cached by call ID.
      if (decision.decision === 'deny') throw new Error('custom-agents: ' + decision.reason.slice(0, 2048));
    },

    prompt: async event => {
      try {
        if (typeof event?.prompt?.text !== 'string') return;
        const cwd = await project(event.sessionID);
        if (cwd) { invalidate(); await run(bindings.prompt.handlers[0], {
          hook_event_name: 'UserPromptSubmit', session_id: event.sessionID, prompt: event.prompt.text, cwd,
        }); }
      } catch { warn(); }
    },

    context: async event => {
      try {
        if (!Array.isArray(event?.system)) return;
        const cwd = await project(event.sessionID);
        if (!cwd) return;
        const revision = generation, before = await signature(cwd);
        let text;
        if (before && cached?.sessionID === event.sessionID && cached.signature === before && Date.now() < cached.until) text = cached.text;
        else {
          const output = await run(bindings.context.handlers[0], {
            hook_event_name: 'SessionStart', source: 'resume', session_id: event.sessionID, cwd,
          });
          text = JSON.parse(output)?.hookSpecificOutput?.additionalContext;
          if (typeof text === 'string' && text) {
            text = text.slice(0, 10000);
            const after = before ? await signature(cwd) : null;
            if (before && revision === generation && before === after && !controller.signal.aborted)
              cached = { sessionID: event.sessionID, text, signature: before, until: Date.now() + 30000 };
          }
        }
        if (typeof text === 'string' && text && !controller.signal.aborted) event.system.push({ type: 'text', text });
      } catch { warn(); }
    },

    'tool-activity': event => {
      // Never awaited by the runtime's tool path: the lookup and the child run in the background,
      // and the child is tracked in `children` for cleanup (design O5, I-05).
      const task = (async () => {
        try {
          if (!event || typeof event.tool !== 'string' || !event.tool) return;
          const cwd = await project(event.sessionID);
          if (!cwd) return;
          const data = { sessionID: event.sessionID, tool: event.tool, status: event.status,
            ...(typeof event.agent === 'string' && event.agent ? { agent: event.agent } : {}), args: summaryArgs(event.input) };
          await run(bindings['tool-activity'].handlers[0], { type: 'tool.execute.after', data, cwd });
        } catch { warn(); }
      })();
      inflight.add(task);
      void task.finally(() => inflight.delete(task));
    },

    post: async event => {
      try {
        if (event?.status !== 'completed') return;
        const cwd = await project(event.sessionID);
        if (!cwd) return;
        if (!readOnly.has(event.tool)) invalidate();
        if (!writing.has(event.tool)) return;
        const input = event.input;
        const native = event.result?.output;
        const targets = Array.isArray(native?.applied) ? native.applied.map(item => item?.target) : [native?.target];
        // Patch moves report the destination in applied; the native diff retains the original.
        if (Array.isArray(native?.files)) for (const file of native.files) {
          const source = typeof file?.patch === 'string' ? file.patch.match(/^--- ([^\r\n]+)$/m)?.[1] : undefined;
          if (source) targets.push(source);
        }
        const paths = [...new Set(targets.filter(path => typeof path === 'string').map(path => path.replaceAll('\\', '/')))];
        const file = input?.filePath ?? input?.file_path ?? input?.path;
        const patch = input?.patchText ?? input?.patch;
        if (!paths.length && typeof file !== 'string' && typeof patch !== 'string') return;
        const payload = {
          hook_event_name: 'PostToolUse', cwd,
          tool_name: paths.length ? 'MultiEdit' : typeof file === 'string' ? 'Edit' : 'apply_patch',
          tool_input: paths.length ? { edits: paths.map(file_path => ({ file_path })) }
            : typeof file === 'string' ? { file_path: file.replaceAll('\\', '/') }
              : { command: patch.split('\n').map(line => line.trimStart()).join('\n') },
        };
        const messages = [];
        for (const script of bindings.post.handlers) {
          const output = await run(script, payload);
          try { const text = JSON.parse(output)?.systemMessage; if (text) messages.push(String(text)); }
          catch { /* A missing diagnostic is not a failed tool execution. */ }
        }
        if (messages.length && event.result) event.result.metadata = {
          ...event.result.metadata, customAgentsMessages: messages,
        };
      } catch { warn(); }
    } };
    // One native registration per event: tool activity and post share execute.after. The unawaited
    // activity binding goes first whatever the catalog order, so the awaited serial post handlers
    // never delay its observation (T-47 fix1).
    const unawaited = new Set(['tool-activity']);
    const registrations = new Map();
    for (const binding of hookCatalog.bindings) {
      if (binding.domain === 'event') continue;
      const name = binding.domain + '.' + binding.native_event;
      if (!registrations.has(name)) registrations.set(name, { binding, list: [] });
      const { list } = registrations.get(name);
      if (unawaited.has(binding.id)) list.unshift(callbacks[binding.id]); else list.push(callbacks[binding.id]);
    }
    for (const { binding, list } of registrations.values()) {
      await ctx[binding.domain].hook(binding.native_event, list.length === 1 ? list[0]
        : async event => { for (const callback of list) await callback(event); });
    }

    const events = (async () => {
      try {
        for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
          const matches = binding => binding.native_events.includes(event.type)
            || (event.type === binding.idle_status_event && event.data?.status?.type === binding.idle_status);
          const activity = matches(bindings.activity), capture = matches(bindings.capture);
          // V2's local stream omits location; session.get remains authoritative in every case.
          if ((!activity && !capture) || (event.location && !sameLocation(event.location, location))) continue;
          try {
            const cwd = await project(event.data?.sessionID);
            if (cwd) { invalidate();
              // Only metadata crosses this boundary; no prompt, response, error or transcript.
              if (activity) await run(bindings.activity.handlers[0], { type: event.type,
                data: { sessionID: event.data.sessionID,
                  ...(event.type === 'session.status' ? { status: { type: event.data.status.type } } : {}) }, cwd });
              if (capture) await run(bindings.capture.handlers[0], {
              hook_event_name: 'SessionEnd', session_id: event.data.sessionID, reason: 'other', cwd,
            }); invalidate(); }
          } catch { warn(); }
        }
      } catch { if (!controller.signal.aborted) warn(); }
    })();
    return async () => {
      controller.abort();
      invalidate();
      const pending = [...children];
      await Promise.all(pending.map(async entry => { await entry.stop(); await entry.done; }));
      await Promise.all([...inflight]);
      await events;
    };
  },
};
