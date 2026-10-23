#!/usr/bin/env python3
"""Validate an opening envelope for the caller; no state writes or approval."""
import argparse
import json
import math
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

MAX_INPUT_BYTES = 512 * 1024
HASH = re.compile(r'[a-f0-9]{64}')
INITIATIVE = re.compile(r'docs/roadmap/[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*')


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError('duplicate_key')
        result[key] = value
    return result


def _constant(_value):
    raise ValueError('nonfinite_value')


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('nonfinite_value')
    return result


def _version(value):
    return (type(value) is dict and set(value) == {'raw_sha256', 'view_sha256', 'view_version'}
            and all(type(value[key]) is str and HASH.fullmatch(value[key])
                    for key in ('raw_sha256', 'view_sha256'))
            and value['view_version'] == 'plan-text-v1')


def validate_open(value, initiative):
    """Bind a complete current plan-ok view, regardless of its first consumer."""
    if (type(initiative) is not str or len(initiative) > 180 or not INITIATIVE.fullmatch(initiative)
            or type(value) is not dict or type(value.get('schema_version')) is not int
            or value['schema_version'] != 1 or value.get('status') != 'ok'):
        raise ValueError('invalid_open')
    review = value.get('review')
    if (type(review) is not dict or review.get('initiative') != initiative
            or review.get('artifact') != 'improvement-plan.md' or review.get('gate_key') != 'plan-ok'
            or review.get('complete') is not True or review.get('validity') != 'current'
            or type(review.get('review_id')) is not str or not HASH.fullmatch(review['review_id'])
            or not _version(review.get('version'))
            or review.get('current_version') != review['version']):
        raise ValueError('invalid_open')
    # First-consumer metadata is history, never caller authentication or approval.
    return {'schema_version': 1, 'status': 'ok', 'review_id': review['review_id'],
            'version': review['version'], 'approval_granted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--initiative', required=True)
    args = parser.parse_args()
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError('input_budget')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                           parse_constant=_constant, parse_float=_float)
        output = validate_open(value, args.initiative)
    except (UnicodeError, ValueError, TypeError, RecursionError):
        print(json.dumps({'schema_version': 1, 'status': 'unavailable', 'reason': 'invalid_open'}))
        return 2
    print(json.dumps(output, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
