import json
from agent_latency_profiler.core import analyze
from agent_latency_profiler.fixtures import generate, EXPECTED
from agent_latency_profiler.report import render

def test_report_matches_ground_truth_exact(tmp_path):
    result = analyze(generate(tmp_path))
    report = json.loads(render(result,'json'))['results']
    assert report['total_ms'] == 66000
    assert report['record_count'] == 200
    assert report['workflow_count'] == 40
    assert report['slow_count'] == 4
    assert [s['p95_ms'] for s in report['stages']] == [100,200,300,400,2000]
    assert [s['max_ms'] for s in report['stages']] == [100,200,300,400,2000]
    assert [s['count'] for s in report['stages']] == [40]*5
    assert sum(s['total_ms'] for s in report['stages']) == report['total_ms']

def test_report_zero_false_positives(tmp_path):
    report = analyze(generate(tmp_path))
    assert {r['id'] for r in report['slow_records']} == set(EXPECTED['slow_ids'])

def test_report_carries_provenance_banner():
    for fmt in ['md','json']:
        assert 'Provenance:' in render(analyze([]),fmt)
        assert 'user-declared' in render(analyze([]),fmt)

def test_hypothetical_figures_labelled():
    for fmt in ['md','json']:
        report = render(analyze([]),fmt)
        assert 'unmeasured' in report and 'hypothetical savings are not computed' in report

def test_no_em_dashes_in_outputs(tmp_path):
    for fmt in ['md','json']:
        assert chr(0x2014) not in render(analyze(generate(tmp_path)),fmt)


def test_failed_replacement_preserves_existing_output(tmp_path,monkeypatch):
    import pytest
    import agent_latency_profiler.report as reporting
    path = tmp_path/'report.md'
    path.write_text('existing')
    def fail(*args):
        raise PermissionError('locked destination')
    monkeypatch.setattr(reporting.os,'replace',fail)
    with pytest.raises(reporting.ReportWriteError):
        reporting.write_atomic(path,'new')
    assert path.read_text() == 'existing'
    assert list(tmp_path.iterdir()) == [path]
