// OpenCode V2 server plugin. Business rules remain in the shared hook services.
import { execFile, spawn } from 'node:child_process';
import { constants, existsSync } from 'node:fs';
import { lstat, open, readdir, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
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
    // One slot per session: a parent and its delegated children never evict each other (gap 11).
    const cache = new Map(), CACHE_SESSIONS = 16;
    let generation = 0;
    const invalidate = () => { cache.clear(); generation++; };
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

    // Only metadata is scanned (journal entries: a digest of the lines the session block quotes);
    // unsafe or oversized trees disable reuse. The signature is the ONLY invalidation: an event never
    // clears the cache, because what it could change is already in the signature (H-46, gap 3).
    const VOLATILE_KEYS = ['materializado_en', 'derivados_en', 'turnos', 'log_hasta', 'reason', 'resumen_por'];
    // `marcadores_cerrados` is not quoted, but whether it is empty decides if an entry is a placeholder: only that signs.
    const VOLATILE_LISTS = ['marcadores_cerrados'];
    // The injected part of a journal entry: its front matter minus what the block never quotes
    // (rewrite timestamps, the turn count, the cost markers). The body is not injected either.
    function injectedDigest(text) {
      const lines = text.split(/\r?\n/);
      if (lines[0] !== '---') return null;
      const end = lines.indexOf('---', 1);
      if (end < 0) return null;
      const kept = [];
      let skipping = null, items = 0;
      const closeList = () => { if (skipping) kept.push(skipping + ':#' + (items > 0)); skipping = null; items = 0; };
      for (const line of lines.slice(1, end)) {
        if (/^\s/.test(line) && skipping) { items++; continue; }
        closeList();
        const list = VOLATILE_LISTS.find(key => line.startsWith(key + ':'));
        if (list) { skipping = list; items = line.includes('[]') ? 0 : (line.slice(list.length + 1).trim() ? 1 : 0); continue; }
        if (VOLATILE_KEYS.some(key => line.startsWith(key + ':'))) continue;
        kept.push(line);
      }
      closeList();
      return createHash('sha1').update(kept.join('\n')).digest('hex');
    }
    async function signature(cwd) {
      const deadline = Date.now() + 1000;
      let count = 0;
      const journalDir = normalized(join(cwd, 'docs', 'knowledge', 'journal'));
      const queueDir = normalized(join(cwd, '.claude', 'journal'));
      const rootRoadmap = normalized(join(cwd, 'docs', 'roadmap'));
      // Rows are returned, never pushed, so siblings can be read concurrently and still sign in name order.
      async function visit(path, depth = 0, top = false) {
        if (++count > 4096 || depth > 12 || Date.now() > deadline) throw new Error('cache bound');
        let info;
        try { info = await lstat(path); }
        catch (error) { if (error.code === 'ENOENT') return [[path, 'missing']]; throw error; }
        if (info.isSymbolicLink()) throw new Error('cache link');
        if (info.isFile() && normalized(dirname(path)) === journalDir) {
          if (!path.endsWith('.md') || path.endsWith('README.md')) return [];   // the index is rebuilt on every write
          if (info.size <= 65536) {
            const digest = injectedDigest(await readFile(path, 'utf8'));
            if (digest) return [[path, 'entry', digest]];
          }
        }
        // A directory signs by name only: its own mtime moves with every file created or rewritten inside it, and the
        // children already sign themselves (a new capture log or marker must not invalidate the cache).
        const rows = [[path, ...(info.isDirectory() ? ['dir'] : [info.dev, info.ino, info.size, info.mtimeMs, info.ctimeMs])]];
        if (!info.isDirectory()) return rows;
        const names = await readdir(path, { withFileTypes: true });
        if (names.length > 4096) throw new Error('cache bound');
        names.sort((a, b) => a.name.localeCompare(b.name));
        const wanted = names.filter(entry => {
          // The per-prompt capture log is volatile and never feeds the session context (H-46).
          if (top && /^session-prompts-.*\.log$/.test(entry.name)) return false;
          // Neither the Confluence pending marker (truncated on every edit under docs/) nor the QA evidence
          // under an initiative's testing/ folder feeds the block (fix2 gaps 8 and 9).
          if (top && entry.name === '.confluence-pending') return false;
          if (entry.name === 'testing' && entry.isDirectory() && normalized(dirname(path)) === rootRoadmap) return false;
          // Envelopes queued by the capture are replayed at the next recompute; only dead letters feed the notice.
          if (normalized(path) === queueDir && ['outbox', 'processing', 'done'].includes(entry.name)) return false;
          return !top || !entry.isDirectory() || entry.name === 'journal';
        });
        for (let index = 0; index < wanted.length; index += 64)
          for (const part of await Promise.all(wanted.slice(index, index + 64).map(entry => visit(join(path, entry.name), depth + 1))))
            rows.push(...part);
        return rows;
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
        const rows = [
          ...await visit(join(cwd, '.claude'), 0, true),
          ...await visit(join(cwd, 'docs', 'roadmap')),
          ...await visit(join(cwd, 'docs', 'knowledge'))];
        return JSON.stringify(rows);
      } catch { return null; }
    }

    // A cache hit must not leave the capture queue to pile up: the envelopes are replayed (oldest first) by a
    // background run of the replay alone (`source: 'drain'`: no index, progress or memory), without delaying the
    // answer. A queue that did not move is tried again after DRAIN_RETRY_MS (a blocked or failed replay leaves it
    // untouched); a queue that changed is drained at once.
    const DRAIN_RETRY_MS = 30000;
    let drained = '', drainedAt = 0;
    async function drainQueue(cwd, sessionID) {
      try {
        const names = (await readdir(join(cwd, '.claude', 'journal', 'outbox'))).filter(name => name.endsWith('.json')).sort().join('|');
        if (!names || (names === drained && Date.now() - drainedAt < DRAIN_RETRY_MS)) return;
        drained = names; drainedAt = Date.now();
        const task = run(bindings.context.handlers[0], { hook_event_name: 'SessionStart', source: 'drain', session_id: sessionID, cwd }).then(() => {});
        inflight.add(task); void task.finally(() => inflight.delete(task));
      } catch { /* No queue, nothing to drain. */ }
    }
    // Only «replay blocked by another replay» describes a moment and is never cached; the permanent notices (damaged
    // queue, outbox.py missing) are cached like any other text.
    const TRANSIENT_NOTICE = 'bloqueado (otro replay en curso)';

    // Session APIs may expose other locations. Never reuse the instance root without checking.
    // `{ directory }` for a session of this location; `{ foreign: true }` for a session whose KNOWN location differs
    // (another workspace: the documented skip); `{}` when the project cannot be told (no session id, an aborted
    // plugin, a session without a location). The guard fails closed on `{}` for the protected roles (T-06 fix7, 10c).
    async function locate(sessionID) {
      if (!sessionID || controller.signal.aborted) return {};
      const response = await ctx.session.get({ sessionID });
      const session = response?.data ?? response;
      if (sameLocation(session?.location, location)) return { directory: session.location.directory };
      return typeof session?.location?.directory === 'string' ? { foreign: true } : {};
    }
    async function project(sessionID) { return (await locate(sessionID)).directory ?? null; }

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
      let decision, protectedRole = false;
      try {
        const guardedIDs = await loadGuardedIDs();
        if (guardedIDs && (!Object.hasOwn(event || {}, 'agent')
            || (typeof event.agent === 'string' && !guardedIDs.has(event.agent)))) return;
        protectedRole = !!guardedIDs && typeof event?.agent === 'string' && guardedIDs.has(event.agent);
        const where = await locate(event.sessionID);
        const cwd = where.directory;
        if (!cwd) {
          if (protectedRole && !where.foreign) throw new Error('project unavailable');
          return;
        }
        const output = await run(bindings.guard.handlers[0], {
          agent: event.agent, tool_name: event.tool, tool_input: event.input, cwd,
        });
        decision = JSON.parse(output);
        if (!['deny', 'continue'].includes(decision?.decision)) throw new Error('guard result');
        if (decision.decision === 'deny' && (typeof decision.reason !== 'string' || !decision.reason.trim()))
          throw new Error('guard result');
        if (decision.diagnostic === 'guardrails-disabled') console.warn('custom-agents: role guards disabled by project configuration');
        else if (decision.diagnostic) warnGuard();
      } catch {
        warnGuard();
        // Fail closed for the protected role (T-06 fix6, ADR-023): no valid decision (deadline, bad output, error)
        // denies the tool call for `implementer`/`architect`; every other identity keeps normal permissions.
        if (protectedRole) throw new Error('custom-agents: the role guard could not decide, so the command is denied for this protected role - retry with a shorter command or ask the user');
        return;
      }
      // A before-hook Error is a native tool failure; no decision is cached by call ID.
      if (decision.decision === 'deny') throw new Error('custom-agents: ' + decision.reason.slice(0, 2048));
    },

    prompt: async event => {
      try {
        if (typeof event?.prompt?.text !== 'string') return;
        const cwd = await project(event.sessionID);
        // No invalidation by event: the context is reused until its signature changes (H-46).
        if (cwd) { await run(bindings.prompt.handlers[0], {
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
        const hit = cache.get(event.sessionID);
        if (before && hit?.signature === before) { text = hit.text; void drainQueue(cwd, event.sessionID); }
        else {
          const output = await run(bindings.context.handlers[0], {
            hook_event_name: 'SessionStart', source: 'resume', session_id: event.sessionID, cwd,
          });
          text = JSON.parse(output)?.hookSpecificOutput?.additionalContext;
          if (typeof text === 'string' && text) {
            text = text.slice(0, 10000);
            const after = before ? await signature(cwd) : null;
            if (before && revision === generation && before === after && !controller.signal.aborted && !text.includes(TRANSIENT_NOTICE)) {
              cache.delete(event.sessionID);
              if (cache.size >= CACHE_SESSIONS) cache.delete(cache.keys().next().value);
              cache.set(event.sessionID, { text, signature: before });
            }
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
            if (cwd) {
              // Only metadata crosses this boundary; no prompt, response, error or transcript.
              if (activity) await run(bindings.activity.handlers[0], { type: event.type,
                data: { sessionID: event.data.sessionID,
                  ...(event.type === 'session.status' ? { status: { type: event.data.status.type } } : {}) }, cwd });
              if (capture) await run(bindings.capture.handlers[0], {
              hook_event_name: 'SessionEnd', session_id: event.data.sessionID, reason: 'other', cwd,
            }); }
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
