// Shared launcher for Claude Code, Codex and OpenCode. No shell interprets the payload.
import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, delimiter, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = dirname(here);
const known = new Set(['session-journal.sh', 'user-prompt-capture.sh', 'session-context.sh',
  'subagent-progress.sh', 'mark-docs-pending.sh', 'ledger-lint-warn.sh', 'progress-line.sh',
  'implementer-guardrail.sh', 'architect-guardrail.sh']);
const hook = process.argv[2];
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
  const py = python();
  if (!py) { warn('Python unavailable; hook skipped'); return; }
  let command, args;
  // Teardown uses native Python directly: no WSL, Bash, find, git or shell startup.
  if (hook === 'session-journal.sh' || hook === 'user-prompt-capture.sh') {
    command = py.command;
    args = [...py.args, join(root, 'agent-kits', 'shared', 'journal.py'),
      hook === 'session-journal.sh' ? 'capture-end' : 'capture'];
    if (env.CLAUDE_PROJECT_DIR) args.push('--root', env.CLAUDE_PROJECT_DIR);
  } else {
    command = windows ? candidates(['bash.exe'])[0] : 'bash';
    if (!command) { warn('Git Bash unavailable; hook skipped'); return; }
    env.CUSTOM_AGENTS_PYTHON = windows ? py.command.replaceAll('\\', '/') : py.command;
    if (windows) {
      env.CLAUDE_PLUGIN_ROOT = root.replaceAll('\\', '/');
      if (env.CLAUDE_PROJECT_DIR) env.CLAUDE_PROJECT_DIR = env.CLAUDE_PROJECT_DIR.replaceAll('\\', '/');
    }
    args = [join(here, 'runtime-entry.sh'), hook];
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
  await new Promise(resolve => {
    const child = spawn(command, args, { env, windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    const timer = setTimeout(() => { child.kill(); resolve(); }, hook === 'session-journal.sh' ? 2200 : 20000);
    let output = '';
    if (post) {
      child.stdout.setEncoding('utf8');
      child.stdout.on('data', chunk => { output += chunk; });
    } else child.stdout.pipe(process.stdout);
    child.stderr.pipe(process.stderr);
    child.stdin.on('error', () => {});
    if (post) child.stdin.end(input, 'utf8');
    else process.stdin.pipe(child.stdin);
    child.on('error', error => { warn(error.message); clearTimeout(timer); resolve(); });
    child.on('close', code => {
      if (post && output.trim()) {
        let message = output.trim();
        try { message = output.trim().split('\n').map(line => JSON.parse(line).systemMessage).filter(Boolean).join('\n'); }
        catch { /* ledger-lint emits plain text; wrap it in the universal message field */ }
        if (message) process.stdout.write(JSON.stringify({ systemMessage: message }) + '\n');
      }
      if (code) warn(`hook failed (${code})`);
      clearTimeout(timer); resolve();
    });
  });
}

main().catch(error => warn(error.message)); // Informational hooks always exit 0.
