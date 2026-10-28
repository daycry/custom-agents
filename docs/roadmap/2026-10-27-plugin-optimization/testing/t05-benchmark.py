#!/usr/bin/env python3
"""Paired before/after statusline benchmark, 10 samples plus one discarded warmup.

Run from the checkout: python docs/roadmap/2026-10-27-plugin-optimization/testing/t05-benchmark.py
The registered-hook benchmark does not include the opt-in statusline. This driver
uses the existing synthetic shell-test project and checks identical output.
"""
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

root = Path.cwd()
sys.path.insert(0, str(root / 'tests'))
from test_hooks_shell import BASH, env_de, proyecto
payload = json.dumps({'model': {'display_name': 'Opus'}, 'cost': {'total_cost_usd': .42},
                      'context_window': {'used_percentage': 8}})
before_source = subprocess.check_output(['git', 'show', 'bae4e46:statusline/roadmap-statusline.sh'])
before = root / '.pytest_cache' / 'statusline-before.sh'
before.parent.mkdir(exist_ok=True)
before.write_bytes(before_source)
after = root / 'statusline/roadmap-statusline.sh'
rows = {name: [] for name in ('before', 'after_cold', 'after_cached')}
report = {'schema_version': 1, 'runs': 10, 'discarded_warmup_per_variant': 1,
          'before_commit': 'bae4e46', 'source_sha256': {
              'before': hashlib.sha256(before_source).hexdigest(),
              'after': hashlib.sha256(after.read_bytes()).hexdigest(),
              'renderer': hashlib.sha256((root / 'agent-kits/shared/statusline-render.py').read_bytes()).hexdigest()},
          'scope': 'Windows Git Bash with the same valid native Python; opt-in statusline only',
          'samples_ms': rows, 'status': 'OK', 'outputs_equal': True}
target = root / 'docs/roadmap/2026-10-27-plugin-optimization/testing/t05-benchmark.json'
try:
    for iteration in range(11):
        values = {}
        outputs = {}
        with tempfile.TemporaryDirectory(prefix='statusline-paired-') as tmp:
            for label, script in [('before', before), ('after_cold', after)]:
                base = Path(tmp) / label;base.mkdir()
                project, _ = proyecto(base)
                env = env_de(project, base)
                def invoke():
                    started = time.perf_counter_ns()
                    result = subprocess.run([BASH, str(script)], input=payload, capture_output=True,
                                            text=True, encoding='utf-8', errors='replace', env=env, cwd=project, timeout=30)
                    elapsed = (time.perf_counter_ns() - started) / 1e6
                    assert result.returncode == 0 and result.stderr == '', (label, result.returncode, result.stderr)
                    return round(elapsed, 3), result.stdout
                values[label], outputs[label] = invoke()
                if label == 'after_cold':
                    values['after_cached'], outputs['after_cached'] = invoke()
        assert len(set(outputs.values())) == 1 and 'T-03/4' in outputs['before'], outputs
        if iteration:
            for label, value in values.items(): rows[label].append(value)
        print(json.dumps({'iteration': iteration, 'warmup': iteration == 0, 'elapsed_ms': values}), flush=True)
except Exception as error:
    report['status'] = 'FALLO'
    report['failure'] = type(error).__name__ + ': ' + str(error)
finally:
    report['median_ms'] = {name: statistics.median(values) if values else None for name, values in rows.items()}
    target.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
sys.exit(0 if report['status'] == 'OK' else 1)
