import json
from agent_latency_profiler.fixtures import generate, EXPECTED
from agent_latency_profiler.cli import load
from agent_latency_profiler.core import analyze

def test_fixtures_labelled_synthetic(tmp_path):
    generate(tmp_path)
    for path in tmp_path.iterdir():
        value = json.loads(path.read_text(encoding='utf-8'))
        assert value['synthetic'] is True
        assert 'Synthetic' in value['_comment']
    assert all(r['synthetic'] for r in load(tmp_path))

def test_fixture_ground_truth_matches_hand_computed(tmp_path):
    generate(tmp_path)
    result = analyze(load(tmp_path))
    for key in ['record_count','workflow_count','total_ms','slow_count']:
        assert result[key] == EXPECTED[key]
    assert {s['stage']:s['total_ms'] for s in result['stages']} == EXPECTED['stage_totals_ms']
    assert [r['id'] for r in result['slow_records']] == EXPECTED['slow_ids']

def test_corrupted_record_changes_figures(tmp_path):
    generate(tmp_path)
    path = tmp_path/'records.json'
    value = json.loads(path.read_text())
    value['records'][4]['duration_ms'] = 500
    path.write_text(json.dumps(value))
    result = analyze(load(tmp_path))
    assert result['total_ms'] == 64500
    assert result['slow_count'] == 3
