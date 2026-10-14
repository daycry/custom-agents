// Child budget per hook for run-hook.mjs. Native guard registrations also leave room for launcher
// startup and confirmed tree cleanup; capture does no deferred work.
//
// SessionEnd in Claude Code has a 1.5 s global budget by default and a plugin's `timeout` does not
// raise it (code.claude.com/docs/en/hooks, «SessionEnd», 2026-10-14). The user can raise it with
// CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS; then this hook may run up to its declared `timeout: 5`.
const SESSION_END_DEFAULT_MS = 1500;
const SESSION_END_HOOK_TIMEOUT_MS = 5000;   // hooks/hooks.json SessionEnd `timeout: 5`
const LAUNCHER_MARGIN_MS = 700;             // launcher startup + tree cleanup inside the budget
const SESSION_END_CHILD_MS = 800;           // SESSION_END_DEFAULT_MS - LAUNCHER_MARGIN_MS

function sessionEndBudgetMs(env) {
  const raw = env.CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS;
  if (typeof raw !== 'string' || !/^[0-9]{1,7}$/.test(raw)) return SESSION_END_DEFAULT_MS;
  return Math.max(SESSION_END_DEFAULT_MS, Number(raw));
}

export function childBudgetMs(hook, runtime, env) {
  if (hook === 'native-guardrail') return 4500;
  if (hook === 'agent-activity') return 2000;
  if (hook !== 'session-journal.sh') return 20000;
  if (runtime !== '--runtime=claude') return 2200;
  const budget = Math.min(sessionEndBudgetMs(env), SESSION_END_HOOK_TIMEOUT_MS);
  return Math.max(SESSION_END_CHILD_MS, budget - LAUNCHER_MARGIN_MS);
}
