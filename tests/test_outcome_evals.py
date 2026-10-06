"""Outcome summaries must derive checks from execution artifacts, not model claims."""
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/outcome-evals/scripts/report_outcomes.py'
spec = importlib.util.spec_from_file_location('outcome_report', SCRIPT)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def make_run(tmp_path, xml='<testsuite><testcase name="contract"/></testsuite>', **changes):
    (tmp_path / 'result.xml').write_text(xml, encoding='utf-8')
    entry = {'id': 'run-1', 'case': 'python-cancel', 'variant': 'baseline', 'revision': 'a' * 40, 'fixture_sha256': 'b' * 64, 'conditions': 'python311-local', 'result': 'result.xml', 'measurements': None}
    entry.update(changes)
    data = {'version': 1, 'runs': [entry]}
    (tmp_path / 'runs.json').write_text(json.dumps(data), encoding='utf-8')
    return tmp_path / 'runs.json'


def test_result_is_derived_from_junit_and_metrics_are_not_invented(tmp_path):
    result = report.summarize(make_run(tmp_path))
    assert result['runs'][0]['outcome'] == 'pass'
    assert result['runs'][0]['measurements'] is None
    assert result['variants']['baseline'] == {'pass': 1, 'fail': 0, 'error': 0, 'not-run': 0}
    assert result['comparable'] is False


def test_b02_cli_redacts_quoted_secret_before_json_serialization(tmp_path, capsys):
    manifest = make_run(tmp_path, result='token="Password123456".xml')
    assert report.main([str(manifest)]) == 0
    output = capsys.readouterr().out
    assert 'Password123456' not in output
    assert '[secreto redactado]' in json.loads(output)['runs'][0]['result']


def test_b03_cli_rejects_extreme_negative_metric_without_traceback(tmp_path, capsys):
    manifest = make_run(tmp_path, measurements={'source': 'manual', 'tokens': -(10 ** 400), 'duration_seconds': None, 'cost_eur': None})
    assert report.main([str(manifest)]) == 2
    output = capsys.readouterr()
    assert output.out == '' and 'unavailable' in output.err and 'Traceback' not in output.err


def test_b02_redaction_collision_cannot_drop_a_variant(tmp_path, capsys):
    manifest = make_run(tmp_path, variant='ghp_' + 'A' * 20)
    data = json.loads(manifest.read_text(encoding='utf-8'))
    data['runs'].append(dict(data['runs'][0], id='run-2', variant='ghp_' + 'B' * 20))
    manifest.write_text(json.dumps(data), encoding='utf-8')
    assert report.main([str(manifest)]) == 2
    assert capsys.readouterr().out == ''


@pytest.mark.parametrize('xml,outcome', [('<testsuite/>', 'not-run'), ('<testsuite><testcase><skipped/></testcase></testsuite>', 'not-run'), ('<testsuite><testcase><failure/></testcase></testsuite>', 'fail'), ('<testsuite><testcase><error/></testcase></testsuite>', 'error')])
def test_failure_error_skip_and_no_cases_are_distinct(tmp_path, xml, outcome):
    assert report.summarize(make_run(tmp_path, xml))['runs'][0]['outcome'] == outcome


def test_two_variants_require_same_cases_fixtures_and_conditions(tmp_path):
    path = make_run(tmp_path)
    data = json.loads(path.read_text(encoding='utf-8'))
    data['runs'].append(dict(data['runs'][0], id='run-2', variant='candidate'))
    path.write_text(json.dumps(data), encoding='utf-8')
    result = report.summarize(path)
    assert result['comparable'] is True
    assert result['variants']['candidate']['pass'] == 1
    data['runs'][1]['conditions'] = 'different-tools'
    path.write_text(json.dumps(data), encoding='utf-8')
    assert report.summarize(path)['comparable'] is False


@pytest.mark.parametrize('changes', [{'id': ''}, {'result': '../outside.xml'}, {'result': 'C:/outside.xml'}, {'revision': 'invented'}, {'fixture_sha256': 'invented'}, {'case': 'secret=Password123456'}, {'measurements': {'tokens': -1}}, {'unexpected': 'field'}])
def test_invalid_inputs_cannot_be_reported_as_success(tmp_path, changes):
    with pytest.raises(ValueError):
        report.summarize(make_run(tmp_path, **changes))


def test_xml_private_contents_are_not_exported(tmp_path):
    path = make_run(tmp_path, '<testsuite><testcase name="token=Password123456"><failure>SECRET FAILURE</failure><system-out>private log</system-out></testcase></testsuite>')
    text = json.dumps(report.summarize(path))
    assert 'Password123456' not in text and 'SECRET FAILURE' not in text and 'private log' not in text


def test_malformed_or_missing_evidence_is_error(tmp_path):
    path = make_run(tmp_path, '<broken')
    assert report.summarize(path)['runs'][0]['outcome'] == 'error'
    (tmp_path / 'result.xml').unlink()
    assert report.summarize(path)['runs'][0]['outcome'] == 'error'


def test_duplicate_runs_are_rejected(tmp_path):
    path = make_run(tmp_path)
    data = json.loads(path.read_text(encoding='utf-8'))
    data['runs'] *= 2
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError):
        report.summarize(path)


def test_cli_emits_report_and_fails_invalid_manifest(tmp_path, capsys):
    path = make_run(tmp_path)
    assert report.main([str(path)]) == 0
    assert json.loads(capsys.readouterr().out)['selection_only'] is False
    path.write_text('{}', encoding='utf-8')
    assert report.main([str(path)]) == 2
    assert capsys.readouterr().out == ''


def test_junit_declared_failure_cannot_be_hidden_by_pass_case(tmp_path):
    path = make_run(tmp_path, '<testsuite tests="1" failures="1"><testcase name="contract"/></testsuite>')
    assert report.summarize(path)['runs'][0]['outcome'] == 'error'


def test_extreme_measurement_is_rejected_without_overflow(tmp_path):
    path = make_run(tmp_path, measurements={'source': 'manual', 'tokens': 10 ** 400, 'duration_seconds': None, 'cost_eur': None})
    with pytest.raises(ValueError):
        report.summarize(path)
