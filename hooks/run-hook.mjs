// Shared launcher for Claude Code, Codex and OpenCode. No shell interprets the payload.
import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, delimiter, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = dirname(here);
const known = new Set(['session-journal.sh', 'user-prompt-capture.sh', 'session-context.sh',
  'subagent-progress.sh', 'mark-docs-pending.sh', 'ledger-lint-warn.sh', 'progress-line.sh',
  'implementer-guardrail.sh', 'architect-guardrail.sh', 'native-guardrail']);
const hook = process.argv[2];
const runtime = process.argv[3] || '--runtime=claude';
const warn = message => process.stderr.write(`custom-agents hooks: ${message}\n`);
const windows = process.platform === 'win32';
const env = { ...process.env, CLAUDE_PLUGIN_ROOT: root, PYTHONIOENCODING: 'utf-8:replace' };

function candidates(names) {
  return (env.PATH || env.Path || '').split(delimiter).filter(Boolean).flatMap(dir =>
    names.map(name => join(dir.replace(/^"|"$/g, ''), name))).filter(path =>
      existsSync(path) && (!windows || !/[/\\](WindowsApps|System32)[/\\]/i.test(path)));
}

function python() {
  const override = env.CUSTOM_AGENTS_PYTHON;
  if (override) return { command: override, args: [] };
  const found = candidates(windows ? ['python3.exe', 'python.exe'] : ['python3', 'python'])[0];
  if (found) return { command: found, args: [] };
  if (windows) {
    const launcher = candidates(['py.exe'])[0];
    if (launcher) {
      const result = spawnSync(launcher, ['-3', '-c', 'import sys;print(sys.executable)'],
        { encoding: 'utf8', timeout: 500, windowsHide: true });
      const executable = result.stdout?.trim();
      if (result.status === 0 && executable && existsSync(executable)) return { command: executable, args: [] };
    }
  }
  return null;
}

async function main() {
  if (!known.has(hook)) { warn('unknown hook'); return; }
  if (!['--runtime=claude', '--runtime=codex', '--runtime=opencode'].includes(runtime)) {
    warn('unknown runtime'); return;
  }
  const py = python();
  if (!py) { warn('Python unavailable; hook skipped'); return; }
  let command, args;
  const guard = hook === 'native-guardrail';
  // Capture and native guards use contained Python without shell startup.
  if (guard || hook === 'session-journal.sh' || hook === 'user-prompt-capture.sh') {
    command = py.command;
    args = guard
      ? [...py.args, '-I', '-S', join(root, 'agent-kits', 'shared', 'native-guardrail.py'),
        '--runtime', runtime.slice('--runtime='.length), '--output', runtime === '--runtime=opencode' ? 'structured' : 'native']
      : hook === 'session-journal.sh'
      ? [...py.args, '-I', '-S', join(root, 'agent-kits', 'shared', 'journal-capture.py')]
      : [...py.args, join(root, 'agent-kits', 'shared', 'journal.py'), 'capture'];
    if (guard) args.push('--project-dir', env.CLAUDE_PROJECT_DIR || process.cwd());
    else if (env.CLAUDE_PROJECT_DIR) args.push('--root', env.CLAUDE_PROJECT_DIR);
  } else {
    command = windows ? candidates(['bash.exe'])[0] : 'bash';
    if (!command) { warn('Git Bash unavailable; hook skipped'); return; }
    env.CUSTOM_AGENTS_PYTHON = windows ? py.command.replaceAll('\\', '/') : py.command;
    if (windows) {
      env.CLAUDE_PLUGIN_ROOT = root.replaceAll('\\', '/');
      if (env.CLAUDE_PROJECT_DIR) env.CLAUDE_PROJECT_DIR = env.CLAUDE_PROJECT_DIR.replaceAll('\\', '/');
    }
    args = [join(here, 'runtime-entry.sh'), hook];
    if (hook === 'session-context.sh') args.push(runtime);
  }
  const post = ['mark-docs-pending.sh', 'ledger-lint-warn.sh', 'progress-line.sh'].includes(hook);
  let input;
  if (post) {
    process.stdin.setEncoding('utf8');
    input = '';
    for await (const chunk of process.stdin) input += chunk;
    try {
      const payload = JSON.parse(input);
      if (payload.tool_name === 'apply_patch' && typeof payload.tool_input?.command === 'string') {
        const paths = [...payload.tool_input.command.matchAll(/^\*\*\* (?:Add File: |Update File: |Delete File: |Move to: )([^\r\n]+)$/gm)]
          .map(match => match[1].replaceAll('\\', '/'));
        payload.tool_input = { edits: [...new Set(paths)].map(file_path => ({ file_path })) };
        input = JSON.stringify(payload);
      }
    } catch { /* malformed input remains informational; shell hooks degrade */ }
  }
  if (windows) {
    const mode = guard || ['session-journal.sh', 'user-prompt-capture.sh'].includes(hook) ? 'python' : 'exec';
    args = [...py.args, '-I', '-S', join(here, 'runtime-supervisor.py'), 'run', String(process.pid), mode, command, ...args];
    command = py.command;
  }
  await new Promise(resolve => {
    const inheritedGroup = !windows && runtime === '--runtime=opencode' && env.CUSTOM_AGENTS_HOOK_OWN_GROUP === '1';
    const child = spawn(command, args, { env, windowsHide: true, detached: !windows && !inheritedGroup, stdio: ['pipe', 'pipe', 'pipe'] });
    let timedOut = false, jobHandle, stopping;
    const abandon = () => {
      child.kill('SIGKILL');
      child.stdout.destroy(); child.stderr.destroy(); child.stdin.destroy();
    };
    const stop = () => {
      if (stopping) return stopping;
      stopping = new Promise(done => {
        if (inheritedGroup || (windows && jobHandle)) {
          const operation = inheritedGroup ? ['close-group', String(process.pid)] : ['close', String(process.pid), jobHandle];
          const cleanup = spawn(py.command, [...py.args, '-I', '-S', join(here, 'runtime-supervisor.py'),
            ...operation], { env, windowsHide: true, detached: inheritedGroup, stdio: 'ignore' });
          const cleanupTimer = setTimeout(() => {
            cleanup.kill('SIGKILL'); warn('child cleanup confirmation timed out'); abandon();
          }, 500);
          cleanup.on('error', () => { clearTimeout(cleanupTimer); warn('child job cleanup unavailable'); abandon(); done(); });
          cleanup.on('close', code => {
            clearTimeout(cleanupTimer);
            if (code) { warn('child job cleanup failed'); abandon(); }
            done();
          });
        } else if (windows) {
          // Before bootstrap confirmation, no business code may run. Closing the
          // launcher also closes any job handle transferred during bootstrap.
          abandon();
          done();
        } else {
          try { process.kill(-child.pid, 'SIGKILL'); }
          catch (error) { if (error.code !== 'ESRCH') { child.kill('SIGKILL'); warn('child tree cleanup failed'); } }
          done();
        }
      });
      return stopping;
    };
    const timer = setTimeout(() => {
      if (!child.pid) return;
      timedOut = true;
      // This is the child budget. Native guard registrations also leave room
      // for launcher startup and confirmed tree cleanup. Capture does no deferred work.
      void stop();
    }, guard ? 4500 : hook === 'session-journal.sh' ? (runtime === '--runtime=claude' ? 800 : 2200) : 20000);
    let output = '';
    if (post) {
      child.stdout.setEncoding('utf8');
      child.stdout.on('data', chunk => { output += chunk; });
    } else child.stdout.pipe(process.stdout);
    if (windows) {
      let header = '', pendingHeader = true;
      child.stderr.setEncoding('utf8');
      child.stderr.on('data', chunk => {
        if (!pendingHeader) { process.stderr.write(chunk); return; }
        header += chunk;
        const end = header.indexOf('\n');
        if (end < 0 && header.length <= 512) return;
        pendingHeader = false;
        try {
          const control = JSON.parse(header.slice(0, end));
          if (control.owner !== process.pid || !/^[1-9][0-9]{0,19}$/.test(control.customAgentsJob)) throw Error();
          jobHandle = control.customAgentsJob;
          if (header.slice(end + 1)) process.stderr.write(header.slice(end + 1));
        } catch { warn('process supervision unavailable; hook skipped'); void stop(); }
        header = '';
      });
    } else child.stderr.pipe(process.stderr);
    child.stdin.on('error', () => {});
    if (post) child.stdin.end(input, 'utf8');
    else process.stdin.pipe(child.stdin);
    child.on('error', error => { warn(error.message); clearTimeout(timer); resolve(); });
    child.on('exit', () => { clearTimeout(timer); void stop(); });
    child.on('close', async code => {
      await stopping;
      if (post && output.trim()) {
        let message = output.trim();
        try { message = output.trim().split('\n').map(line => JSON.parse(line).systemMessage).filter(Boolean).join('\n'); }
        catch { /* ledger-lint emits plain text; wrap it in the universal message field */ }
        if (message) process.stdout.write(JSON.stringify({ systemMessage: message }) + '\n');
      }
      if (timedOut) warn(hook === 'session-journal.sh'
        ? 'capture timed out; journal recover can reconcile the retained prompt log'
        : 'hook timed out');
      else if (code) warn(`hook failed (${code})`);
      clearTimeout(timer); resolve();
    });
  });
}

main().catch(error => warn(error.message)); // Informational hooks always exit 0.
