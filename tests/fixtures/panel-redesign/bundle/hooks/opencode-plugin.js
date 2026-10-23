// Fixture: solo el catálogo de hooks (dato, no código ejecutable).
// custom-agents hook-catalog:start
const hookCatalog = JSON.parse(`{
  "schema_version": 1,
  "bindings": [
    {"id":"guard","domain":"tool","native_event":"execute.before","event":"PreToolUse","handlers":["native-guardrail"],"timeout_ms":10500,"behavior":"guard","activation":"Exact own implementer and architect agent IDs; current project location"},
    {"id":"prompt","domain":"session","native_event":"prompt","event":"UserPromptSubmit","handlers":["user-prompt-capture.sh"],"timeout_ms":20000,"behavior":"informative","activation":"Text prompt in the current project location"},
    {"id":"context","domain":"session","native_event":"context","event":"SessionStart","handlers":["session-context.sh"],"timeout_ms":20000,"behavior":"informative","activation":"System context array in the current project location; unchanged context may reuse its cache"},
    {"id":"post","domain":"tool","native_event":"execute.after","event":"PostToolUse","handlers":["mark-docs-pending.sh","ledger-lint-warn.sh","progress-line.sh"],"timeout_ms":20000,"behavior":"informative","activation":"Completed writing tool in the current project location","tools":["edit","write","patch","multiedit","apply_patch"]},
    {"id":"capture","domain":"event","native_events":["session.execution.succeeded","session.execution.failed","session.execution.interrupted","session.idle"],"idle_status_event":"session.status","idle_status":"idle","event":"SessionEnd","handlers":["session-journal.sh"],"timeout_ms":20000,"behavior":"informative","activation":"Execution/idle stream observation in the current project location; not a teardown hook"},
    {"id":"tool-activity","domain":"tool","native_event":"execute.after","event":"PostToolUse","handlers":["agent-activity"],"timeout_ms":2500,"behavior":"informative","activation":"Opt-in tool observation after exact project location verification; dispatched without waiting for the child"},
    {"id":"activity","domain":"event","native_events":["session.execution.started","session.execution.succeeded","session.execution.failed","session.execution.interrupted","session.idle"],"idle_status_event":"session.status","idle_status":"idle","event":"ActivityObserved","handlers":["agent-activity"],"timeout_ms":2500,"behavior":"informative","activation":"Opt-in execution start/end and idle observations after exact project location verification; not liveness or teardown"}
  ]
}`);
// custom-agents hook-catalog:end
