// OpenCode V2 server plugin. Business rules remain in the shared hook services.
import { execFile, spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { lstat, open, readdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const home = process.env.HOME || process.env.USERPROFILE || '.';
const postHooks = ['mark-docs-pending.sh', 'ledger-lint-warn.sh', 'progress-line.sh'];
const writing = new Set(['edit', 'write', 'patch', 'multiedit', 'apply_patch']);
const readOnly = new Set(['read', 'glob', 'grep', 'list', 'ls', 'webfetch', 'websearch']);
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
    const children = new Set();
    let cached, generation = 0;
    const invalidate = () => { cached = undefined; generation++; };
    const warn = () => console.warn('custom-agents: informational hook unavailable; continuing');

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
        let child, timer, finished = false, output = '', diagnostic = false, cancelled = false, stopping;
        let settle;
        const done = new Promise(resolveDone => { settle = resolveDone; });
        const entry = { done, stop: () => {
          if (stopping) return stopping;
          cancelled = true;
          stopping = new Promise(resolveStop => {
            if (!child?.pid) return resolveStop();
            if (process.platform === 'win32') {
              execFile('taskkill', ['/PID', String(child.pid), '/T', '/F'], { windowsHide: true }, () => resolveStop());
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
          child = spawn('node', [join(hooks, 'run-hook.mjs'), script], {
            cwd: payload.cwd, windowsHide: true, detached: process.platform !== 'win32',
            env: { ...process.env, CLAUDE_PROJECT_DIR: payload.cwd },
            stdio: ['pipe', 'pipe', 'pipe'],
          });
          children.add(entry);
          timer = setTimeout(() => { warn(); void entry.stop(); }, 20000);
          child.stdout.setEncoding('utf8');
          child.stdout.on('data', chunk => {
            if (cancelled) return;
            output += chunk;
            if (output.length > 65536) { output = ''; warn(); void entry.stop(); }
          });
          child.stderr.on('data', () => { diagnostic = true; }); // Never log payloads or consumer paths.
          child.stdin.on('error', () => {});
          child.on('error', () => { diagnostic = true; warn(); });
          child.on('close', async code => { await stopping; if (code || diagnostic) warn(); finish(code || cancelled ? '' : output); });
          child.stdin.end(JSON.stringify(payload), 'utf8');
        } catch { warn(); if (child?.pid) void entry.stop(); else finish(''); }
      });
    }

    await ctx.session.hook('prompt', async event => {
      try {
        if (typeof event?.prompt?.text !== 'string') return;
        const cwd = await project(event.sessionID);
        if (cwd) { invalidate(); await run('user-prompt-capture.sh', {
          hook_event_name: 'UserPromptSubmit', session_id: event.sessionID, prompt: event.prompt.text, cwd,
        }); }
      } catch { warn(); }
    });

    await ctx.session.hook('context', async event => {
      try {
        if (!Array.isArray(event?.system)) return;
        const cwd = await project(event.sessionID);
        if (!cwd) return;
        const revision = generation, before = await signature(cwd);
        let text;
        if (before && cached?.sessionID === event.sessionID && cached.signature === before && Date.now() < cached.until) text = cached.text;
        else {
          const output = await run('session-context.sh', {
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
    });

    await ctx.tool.hook('execute.after', async event => {
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
        for (const script of postHooks) {
          const output = await run(script, payload);
          try { const text = JSON.parse(output)?.systemMessage; if (text) messages.push(String(text)); }
          catch { /* A missing diagnostic is not a failed tool execution. */ }
        }
        if (messages.length && event.result) event.result.metadata = {
          ...event.result.metadata, customAgentsMessages: messages,
        };
      } catch { warn(); }
    });

    const events = (async () => {
      try {
        for await (const event of ctx.event.subscribe({ signal: controller.signal })) {
          const idle = ['session.execution.succeeded', 'session.execution.failed', 'session.execution.interrupted', 'session.idle'].includes(event.type)
            || (event.type === 'session.status' && event.data?.status?.type === 'idle');
          // V2's local stream omits location; session.get remains authoritative in every case.
          if (!idle || (event.location && !sameLocation(event.location, location))) continue;
          try {
            const cwd = await project(event.data?.sessionID);
            if (cwd) { invalidate(); await run('session-journal.sh', {
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
      await events;
    };
  },
};
