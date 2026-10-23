#!/usr/bin/env python3
"""Summarize bounded JUnit execution artifacts; never execute tests or approve QA."""
import argparse
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
import xml.etree.ElementTree as ET

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

MAX_BYTES = 2 * 1024 * 1024
MAX_RUNS = 1000
OUTCOMES = ('pass', 'fail', 'error', 'not-run')
FIELDS = {'id', 'case', 'variant', 'revision', 'fixture_sha256', 'conditions', 'result', 'measurements'}


# --8<-- cloud path guard SHARED
def _linked(path):
    try:
        info = path.lstat()
        if path.is_symlink():
            return True
        if not getattr(info, 'st_file_attributes', 0) & 0x400:
            return False
        # Windows CLOUD variants describe sync placeholders, not path redirects.
        # Unknown reparse tags stay excluded, including junctions and symlinks.
        tag = getattr(info, 'st_reparse_tag', 0)
        return (tag & 0xFFFF0FFF) != 0x9000001A
    except FileNotFoundError:
        return False
# --8<-- end cloud path guard SHARED


def _read(path):
    if any(_linked(p) for p in (path, *path.absolute().parents)):
        raise ValueError('linked evidence')
    with path.open('rb') as handle:
        content = handle.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError('evidence exceeds limit')
    return content.decode('utf-8-sig')


def _evidence(root, relative):
    if not isinstance(relative, str) or len(relative) > 200 or '\\' in relative or PureWindowsPath(relative).drive or PurePosixPath(relative).is_absolute() or '..' in PurePosixPath(relative).parts or not relative.endswith('.xml'):
        raise ValueError('expected relative XML evidence path')
    return root / relative


def _measurements(value):
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {'source', 'tokens', 'duration_seconds', 'cost_eur'} or value['source'] not in ('usage-meter', 'runner', 'manual'):
        raise ValueError('measurement source and fields required')
    for key in ('tokens', 'duration_seconds', 'cost_eur'):
        number = value[key]
        if number is not None and (type(number) not in (int, float) or not 0 <= number <= 10 ** 18 or not math.isfinite(number) or (key == 'tokens' and type(number) is not int)):
            raise ValueError('invalid measurement')
    return dict(value)


def _counts(document):
    counts = {'passed': 0, 'failed': 0, 'errors': 0, 'skipped': 0}
    for testcase in document.iter('testcase'):
        key = 'errors' if testcase.find('error') is not None else 'failed' if testcase.find('failure') is not None else 'skipped' if testcase.find('skipped') is not None else 'passed'
        counts[key] += 1
    return counts


def _verify_junit(document):
    pending = [(document, 0)]
    while pending:
        element, depth = pending.pop()
        if depth > 32:
            raise ValueError('XML nesting limit exceeded')
        pending.extend((child, depth + 1) for child in element)
    for suite in document.iter():
        if suite.tag not in ('testsuite', 'testsuites'):
            continue
        counts = _counts(suite)
        expected = {'tests': sum(counts.values()), 'failures': counts['failed'], 'errors': counts['errors'], 'skipped': counts['skipped']}
        for field, count in expected.items():
            declared = suite.get(field)
            if declared is not None and (not re.fullmatch(r'[0-9]{1,12}', declared) or int(declared) != count):
                raise ValueError('JUnit counts disagree with test cases')


def _run(entry, root):
    if not isinstance(entry, dict) or set(entry) != FIELDS:
        raise ValueError('invalid run schema')
    for key in ('id', 'case', 'variant', 'conditions'):
        if not isinstance(entry[key], str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,63}', entry[key]):
            raise ValueError('invalid run identifier')
    for key, width in (('revision', 40), ('fixture_sha256', 64)):
        if not isinstance(entry[key], str) or not re.fullmatch(r'[0-9a-f]{' + str(width) + '}', entry[key]):
            raise ValueError('invalid revision or fixture fingerprint')
    evidence = _evidence(root, entry['result'])
    measurements = _measurements(entry['measurements'])
    counts = {'passed': 0, 'failed': 0, 'errors': 0, 'skipped': 0}
    try:
        raw = _read(evidence)
        if '<!DOCTYPE' in raw.upper() or '<!ENTITY' in raw.upper():
            raise ValueError('DTD not allowed')
        document = ET.fromstring(raw)
        if document.tag not in ('testsuites', 'testsuite'):
            raise ValueError('expected JUnit suite')
        _verify_junit(document)
        counts = _counts(document)
        outcome = 'error' if counts['errors'] else 'fail' if counts['failed'] else 'not-run' if counts['skipped'] or not counts['passed'] else 'pass'
    except (OSError, ValueError, UnicodeError, ET.ParseError):
        outcome = 'error'
    return {**{key: entry[key] for key in ('id', 'case', 'variant', 'revision', 'fixture_sha256', 'conditions', 'result')}, 'outcome': outcome, 'checks': counts, 'measurements': measurements}


def summarize(path):
    path = Path(path).absolute()
    data = json.loads(_read(path))
    if not isinstance(data, dict) or set(data) != {'version', 'runs'} or type(data['version']) is not int or data['version'] != 1 or not isinstance(data['runs'], list) or not 1 <= len(data['runs']) <= MAX_RUNS:
        raise ValueError('invalid outcome manifest')
    runs = [_run(entry, path.parent) for entry in data['runs']]
    if len({run['id'] for run in runs}) != len(runs):
        raise ValueError('duplicate run identifier')
    variants, conditions = {}, {}
    for run in runs:
        variants.setdefault(run['variant'], dict.fromkeys(OUTCOMES, 0))[run['outcome']] += 1
        signatures = conditions.setdefault(run['variant'], {})
        signature = (run['case'], run['fixture_sha256'], run['conditions'])
        signatures[signature] = signatures.get(signature, 0) + 1
    comparable = len(conditions) >= 2 and all(value == next(iter(conditions.values())) for value in conditions.values())
    return {'version': 1, 'evidence': 'junit execution artifacts; metadata and measurements reported by producer', 'selection_only': False, 'qa_approval': False, 'comparable': comparable, 'runs': runs, 'variants': dict(sorted(variants.items()))}


def _redact(value):
    path = Path(__file__).resolve().parents[3] / 'agent-kits/shared/redact.py'
    if not path.is_file() or _linked(path):
        raise ValueError('bundled redactor unavailable')
    spec = importlib.util.spec_from_file_location('outcome_redactor', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    def clean(item):
        if isinstance(item, str):
            return module.redactar(item)
        if isinstance(item, list):
            return [clean(child) for child in item]
        if isinstance(item, dict):
            result = {}
            for key, child in item.items():
                safe_key = module.redactar(key)
                if safe_key in result:
                    raise ValueError('redaction would merge distinct identifiers')
                result[safe_key] = clean(child)
            return result
        return item
    return clean(value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(_redact(summarize(args.manifest)), ensure_ascii=False))
        return 0
    except (OSError, ValueError, UnicodeError, RecursionError):
        print('outcome report unavailable: check manifest, evidence and bundled redactor', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
